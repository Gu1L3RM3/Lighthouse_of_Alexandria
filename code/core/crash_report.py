"""Make a crash visible outside the game.

In the browser a Python traceback never reaches the JavaScript console, so
whoever hosts the game has to be told explicitly.
"""

from collections.abc import Awaitable, Callable


async def run_reporting_crashes(
    run: Callable[[], Awaitable[None]], report: Callable[[str], None]
) -> None:
    try:
        await run()
    except Exception as error:
        report(f"{type(error).__name__}: {error}")
        raise
