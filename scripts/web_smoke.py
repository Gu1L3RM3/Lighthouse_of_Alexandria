"""Build the web version and play its first screens in headless Chromium.

    python scripts/web_smoke.py [--out DIR]
    python scripts/web_smoke.py --serve        # only build and serve, for manual or MCP testing

Boots on a desktop and on a landscape phone (with a real touch tap), and fails
on a Python crash, a JavaScript error, a boot that stalls, a blank canvas or a
local-only folder inside the bundle. The pygbag runtime comes from its CDN, so
this needs network access.
"""

import argparse
import contextlib
import functools
import io
import subprocess
import sys
import tarfile
import tempfile
import threading
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sandbox import copy_project

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_NAME = "alexandria"
BUILD_TIMEOUT_SECONDS = 300
BOOT_TIMEOUT_MS = 120_000
SCREEN_TIMEOUT_MS = 30_000
SETTLE_MS = 3_000
TAP_HOLD_MS = 120
LOGICAL_SIZE = (1280, 720)
# Centre of "New journey" on the main menu, in the game's 1280x720 coordinates.
NEW_JOURNEY_BUTTON = (640, 433)
# The animated menu changes a few pixels by itself; a new screen changes far more.
MIN_TAP_CHANGE = 0.25
MIN_DRAWN_COLORS = 16
NEVER_SHIPPED = (".claude", ".github", ".playwright-mcp", "scripts", "paper_figures", "site", "tools")


@dataclass(frozen=True)
class Target:
    name: str
    width: int
    height: int
    touch: bool


TARGETS = (
    Target("desktop-1280x720", 1280, 720, touch=False),
    Target("phone-844x390", 844, 390, touch=True),
)


@dataclass
class PageRun:
    boot: str = "download"
    crash: str = ""
    page_errors: list[str] = field(default_factory=list)
    frame: bytes = b""
    after_tap: bytes = b""


def _pixels(png: bytes):
    from PIL import Image

    return Image.open(io.BytesIO(png)).convert("RGB").resize((160, 90))


def is_blank(png: bytes) -> bool:
    return _pixels(png).getcolors(MIN_DRAWN_COLORS) is not None


def changed_ratio(before: bytes, after: bytes) -> float:
    from PIL import ImageChops

    difference = ImageChops.difference(_pixels(before), _pixels(after)).convert("L")
    unchanged = difference.point(lambda value: 255 if value <= 8 else 0).histogram()[255]
    return 1 - unchanged / (difference.width * difference.height)


def failure_reason(run: PageRun) -> str | None:
    if run.crash:
        return f"the game crashed: {run.crash}"
    if run.page_errors:
        return f"JavaScript error: {run.page_errors[0]}"
    if run.boot != "done":
        return (
            f"the boot stopped at '{run.boot}' "
            "(the runtime is downloaded from pygame-web.github.io: is the network up?)"
        )
    if not run.frame or is_blank(run.frame):
        return "the canvas stayed blank"
    if run.after_tap and changed_ratio(run.frame, run.after_tap) < MIN_TAP_CHANGE:
        return "the tap on 'New journey' did not change the screen"
    return None


def to_page(point: tuple[int, int], canvas: dict) -> tuple[float, float]:
    return (
        canvas["x"] + point[0] / LOGICAL_SIZE[0] * canvas["width"],
        canvas["y"] + point[1] / LOGICAL_SIZE[1] * canvas["height"],
    )


def bundle_leaks(archive: Path) -> list[str]:
    with tarfile.open(archive) as tar:
        top_folders = {
            parts[1] for name in tar.getnames() if len(parts := name.split("/")) > 2 and parts[0] == "assets"
        }
    return sorted(top_folders & set(NEVER_SHIPPED))


def build(scratch: Path) -> Path:
    project = copy_project(PROJECT_ROOT, scratch / BUNDLE_NAME)
    result = subprocess.run(
        [
            sys.executable, "-m", "pygbag",
            "--template", "web/alexandria.tmpl",
            "--icon", "assets/images/icon/game_icon_64.png",
            "--build", ".",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=BUILD_TIMEOUT_SECONDS,
    )
    web = project / "build" / "web"
    if result.returncode != 0 or not (web / "index.html").is_file():
        raise RuntimeError(f"pygbag build failed:\n{(result.stdout + result.stderr)[-3000:]}")
    return web


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextlib.contextmanager
def serving(directory: Path, port: int = 0):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        server.server_close()


def _wait_for_drawn_canvas(page) -> bytes:
    for _ in range(SCREEN_TIMEOUT_MS // SETTLE_MS):
        page.wait_for_timeout(SETTLE_MS)
        frame = page.screenshot()
        if page.get_attribute("body", "data-crash") or not is_blank(frame):
            return frame
    return page.screenshot()


def _tap(page, point: tuple[float, float]) -> None:
    session = page.context.new_cdp_session(page)
    touch = [{"x": point[0], "y": point[1]}]
    session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": touch})
    page.wait_for_timeout(TAP_HOLD_MS)
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def play(browser, url: str, target: Target) -> PageRun:
    context = browser.new_context(
        viewport={"width": target.width, "height": target.height},
        has_touch=target.touch,
        is_mobile=target.touch,
        locale="en-US",
    )
    page = context.new_page()
    run = PageRun()
    page.on("pageerror", lambda error: run.page_errors.append(str(error)))
    try:
        page.goto(url)
        # "ready" means the page waits for a click to unlock audio; some browsers skip it.
        page.wait_for_function(
            "['ready', 'done'].includes(document.body.dataset.boot)", timeout=BOOT_TIMEOUT_MS
        )
        if page.get_attribute("body", "data-boot") == "ready":
            page.mouse.click(target.width / 2, target.height / 2)
        page.wait_for_function("document.body.dataset.boot === 'done'", timeout=BOOT_TIMEOUT_MS)
        run.frame = _wait_for_drawn_canvas(page)
        if target.touch and not page.get_attribute("body", "data-crash"):
            canvas = page.locator("#canvas").bounding_box()
            _tap(page, to_page(NEW_JOURNEY_BUTTON, canvas))
            page.wait_for_timeout(SETTLE_MS)
            run.after_tap = page.screenshot()
    except Exception as error:  # a stalled boot is a result, reported below
        if "Timeout" not in type(error).__name__:
            raise
    finally:
        run.boot = page.get_attribute("body", "data-boot") or "unknown"
        run.crash = page.get_attribute("body", "data-crash") or ""
        context.close()
    return run


def serve_until_interrupted(port: int) -> int:
    with tempfile.TemporaryDirectory() as folder:
        web = build(Path(folder))
        with serving(web, port) as url:
            print(f"web: serving {url} (Ctrl+C to stop)", flush=True)
            with contextlib.suppress(KeyboardInterrupt):
                threading.Event().wait()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="screenshot folder (default: a new temp folder)")
    parser.add_argument("--serve", action="store_true", help="build, serve and wait for Ctrl+C")
    parser.add_argument("--port", type=int, default=0, help="port for --serve (default: any free one)")
    options = parser.parse_args(argv)
    if options.serve:
        return serve_until_interrupted(options.port)
    out_dir = (options.out or Path(tempfile.mkdtemp(prefix="alexandria-web-"))).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    failures = 0
    with tempfile.TemporaryDirectory() as folder:
        web = build(Path(folder))
        leaks = bundle_leaks(web / f"{BUNDLE_NAME}.tar.gz")
        if leaks:
            failures += 1
            print(f"FAIL bundle: local-only folders were packed: {', '.join(leaks)}")
        with serving(web) as url, sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for target in TARGETS:
                run = play(browser, url, target)
                for suffix, png in (("", run.frame), ("-after-tap", run.after_tap)):
                    if png:
                        (out_dir / f"{target.name}{suffix}.png").write_bytes(png)
                reason = failure_reason(run)
                failures += bool(reason)
                print(f"{'FAIL' if reason else 'PASS'} {target.name}: {reason or 'booted and drawn'}")
            browser.close()
    print(f"web: {'FAILED' if failures else 'OK'}, screenshots in {out_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
