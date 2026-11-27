# /// script
# dependencies = [
#     "pytmx",
#     "pathfinding",
# ]
# ///
# The block above tells pygbag (web build) which pure-Python wheels to fetch;
# desktop builds read requirements.txt instead. pygbag 0.9.3 rejects version pins here.

from pathlib import Path
import asyncio
import sys

# pygbag resolves `pygame.locals` (used by core.settings) only after pygame itself is imported.
import pygame  # noqa: F401


PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from core.crash_report import run_reporting_crashes
from core.settings import CIRCUITOS_DIR, IS_WEB, SAVE_DIR


def build_storage_sync():
    if not IS_WEB:
        return None
    import platform  # pygbag's module, exposes the browser `window`
    from core.telemetry.browser import read_storage_prefix
    from core.web_storage_sync import WebStorageSync

    sync = WebStorageSync(
        CIRCUITOS_DIR.parent,
        [CIRCUITOS_DIR, SAVE_DIR],
        platform.window.localStorage,
        key_prefix=read_storage_prefix(platform.window),
    )
    sync.restore()
    return sync


def build_telemetry_options() -> dict:
    """Research telemetry stays off unless the hosting page defines `window.alexTelemetry`."""
    if not IS_WEB:
        return {}
    import platform
    from core.telemetry import TelemetryService
    from core.telemetry.browser import create_transport, read_viewport_size, read_visibility_state

    window = platform.window
    return {
        "telemetry": TelemetryService(transport=create_transport(sys.platform, window)),
        "visibility_reader": lambda: read_visibility_state(window),
        "viewport": read_viewport_size(window),
    }


def report_crash(message: str) -> None:
    if not IS_WEB:
        return
    import platform

    # scripts/web_smoke.py reads this: browser consoles never see Python tracebacks.
    platform.window.document.body.setAttribute("data-crash", message)


async def run_game():
    # Restore saved data before the game imports read circuits or saves.
    storage_sync = build_storage_sync()
    from game import Game

    await Game(storage_sync=storage_sync, **build_telemetry_options()).run()


async def main():
    await run_reporting_crashes(run_game, report_crash)


if __name__ == "__main__":
    asyncio.run(main())
