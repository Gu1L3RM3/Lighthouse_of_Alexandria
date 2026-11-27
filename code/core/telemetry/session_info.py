from pathlib import Path

VERSION_FILE = "VERSION"
UNKNOWN_VERSION = "dev"


def read_game_version(search_dirs: list[Path]) -> str:
    """The release pipeline writes a VERSION file next to the build; source runs report "dev"."""
    for directory in search_dirs:
        try:
            version = (Path(directory) / VERSION_FILE).read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if version:
            return version
    return UNKNOWN_VERSION


def record_session_start(telemetry, *, game_version, language, is_web, viewport, input_source) -> None:
    width, height = viewport if viewport else (None, None)
    telemetry.record(
        "session_start",
        game_version=game_version,
        language=language,
        platform="web" if is_web else "desktop",
        viewport_w=width,
        viewport_h=height,
        input_source=input_source,
    )
