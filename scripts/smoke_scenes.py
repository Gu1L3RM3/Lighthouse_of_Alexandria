"""Boot every registered scene headless and save what each one draws.

    python scripts/smoke_scenes.py [scene ...] [--out DIR] [--seconds N]

Runs in a throwaway copy of the project, so saves and circuit files are safe.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sandbox import copy_project

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_TIMEOUT_SECONDS = 90
DEFAULT_SECONDS = 1.5
EDITOR_RUN = "circuit_editor"
EDITOR_FILE = "final_fase/fase_8/pannel4"
# Scenes that cannot be opened on their own, with the reason. Keep it empty if possible.
SKIPPED_SCENES: dict[str, str] = {}
LIST_SCENES = (
    "import sys; sys.path.insert(0, 'code');"
    "from game import Game; from core.managers.scene_manager import SceneManager;"
    "Game(); print('SCENES=' + ','.join(SceneManager.get().scene_names()))"
)


def failure_reason(returncode: int, output: str, screenshot: Path) -> str | None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if "Traceback (most recent call last)" in output:
        return lines[-1]
    if returncode != 0:
        return f"exit {returncode}: {lines[-1] if lines else 'no output'}"
    for line in lines:
        if "[ALEX_PROFILE] warning" in line:
            return line
    if not screenshot.is_file():
        return "no screenshot was saved"
    return None


def select_scenes(registered: list[str], requested: list[str]) -> list[str]:
    unknown = sorted(set(requested) - set(registered))
    if unknown:
        raise ValueError(f"unknown scene(s): {', '.join(unknown)}")
    return requested or registered


def headless_environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("ALEX_")}
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONDONTWRITEBYTECODE="1")
    return env


def registered_scenes(project: Path) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-c", LIST_SCENES],
        cwd=project,
        env=headless_environment(),
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_SECONDS,
    )
    for line in result.stdout.splitlines():
        if line.startswith("SCENES="):
            return line.removeprefix("SCENES=").split(",")
    raise RuntimeError(f"could not list the scenes:\n{result.stderr.strip()}")


def run_scene(base: Path, scratch: Path, name: str, out_dir: Path, seconds: float) -> str | None:
    # One copy per scene: runs are parallel and each one writes its own saves.
    project = scratch / name
    shutil.copytree(base, project)
    screenshot = out_dir / f"{name}.png"
    screenshot.unlink(missing_ok=True)
    env = headless_environment()
    env.update(ALEX_PROFILE_SECONDS=str(seconds), ALEX_SCREENSHOT_PATH=str(screenshot))
    if name == EDITOR_RUN:
        env.update(ALEX_BOOT_EDITOR_FILE=EDITOR_FILE, ALEX_BOOT_EDITOR_DEBUG="1")
    else:
        env["ALEX_START_SCENE"] = name
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"timed out after {RUN_TIMEOUT_SECONDS}s"
    finally:
        shutil.rmtree(project, ignore_errors=True)
    return failure_reason(result.returncode, result.stdout + result.stderr, screenshot)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scenes", nargs="*", help=f"scene names ({EDITOR_RUN} boots the editor)")
    parser.add_argument("--out", type=Path, help="screenshot folder (default: a new temp folder)")
    parser.add_argument("--seconds", type=float, default=DEFAULT_SECONDS)
    options = parser.parse_args(argv)
    out_dir = (options.out or Path(tempfile.mkdtemp(prefix="alexandria-smoke-"))).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as folder:
        scratch = Path(folder)
        base = copy_project(PROJECT_ROOT, scratch / "_base")
        names = select_scenes(registered_scenes(base) + [EDITOR_RUN], options.scenes)
        # The listing boot wrote saves into the base copy; start every scene from a clean one.
        shutil.rmtree(base)
        copy_project(PROJECT_ROOT, base)
        runnable = [name for name in names if name not in SKIPPED_SCENES]
        with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
            reasons = list(
                pool.map(lambda name: run_scene(base, scratch, name, out_dir, options.seconds), runnable)
            )

    for name in names:
        if name in SKIPPED_SCENES:
            print(f"SKIPPED {name}: {SKIPPED_SCENES[name]}")
    failures = [(name, reason) for name, reason in zip(runnable, reasons) if reason]
    for name, reason in failures:
        print(f"FAIL {name}: {reason}")
    print(f"smoke: {len(runnable) - len(failures)}/{len(runnable)} scenes OK, screenshots in {out_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
