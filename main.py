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

from core.settings import CIRCUITOS_DIR, IS_WEB, SAVE_DIR


def build_storage_sync():
    if not IS_WEB:
        return None
    import platform  # pygbag's module, exposes the browser `window`
    from core.web_storage_sync import WebStorageSync

    sync = WebStorageSync(CIRCUITOS_DIR.parent, [CIRCUITOS_DIR, SAVE_DIR], platform.window.localStorage)
    sync.restore()
    return sync


async def main():
    # Restore saved data before the game imports read circuits or saves.
    storage_sync = build_storage_sync()
    from game import Game

    await Game(storage_sync=storage_sync).run()


if __name__ == "__main__":
    asyncio.run(main())
