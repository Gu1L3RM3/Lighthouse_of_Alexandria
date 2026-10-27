import json
from dataclasses import asdict, dataclass
from pathlib import Path

from core.settings import (
    GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL,
    GENERIC_LEVEL_GHOST_RESPAWN_SECONDS,
    GENERIC_LEVEL_TOLERANCE_PERCENT,
    LEVEL_CONFIG_FILE,
    path_in_circuitos,
)


class LevelConfigError(ValueError):
    pass


@dataclass(frozen=True)
class LevelConfig:
    """Per-level tuning kept next to the level's circuits, so teachers can change it without code."""

    title: str = ""
    tolerance_percent: float = GENERIC_LEVEL_TOLERANCE_PERCENT
    bomb_count: int = GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL
    ghost_respawn_seconds: float = GENERIC_LEVEL_GHOST_RESPAWN_SECONDS

    @classmethod
    def load(cls, path: Path) -> "LevelConfig":
        path = Path(path)
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LevelConfigError(f"{path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise LevelConfigError(f"{path}: expected a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def for_level(cls, level_path: str) -> "LevelConfig":
        return cls.load(path_in_circuitos(level_path, LEVEL_CONFIG_FILE))

    @classmethod
    def from_dict(cls, payload: dict) -> "LevelConfig":
        return cls(
            title=str(payload.get("title", "")),
            tolerance_percent=_non_negative(payload, "tolerance_percent", float, GENERIC_LEVEL_TOLERANCE_PERCENT),
            bomb_count=_non_negative(payload, "bomb_count", int, GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL),
            ghost_respawn_seconds=_non_negative(
                payload, "ghost_respawn_seconds", float, GENERIC_LEVEL_GHOST_RESPAWN_SECONDS
            ),
        )

    def to_dict(self) -> dict:
        defaults = asdict(LevelConfig())
        return {name: value for name, value in asdict(self).items() if value != defaults[name]}

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _non_negative(payload: dict, key: str, kind: type, default):
    raw = payload.get(key, default)
    if isinstance(raw, bool):
        raise LevelConfigError(f"{key} must be a number")
    try:
        value = kind(raw)
    except (TypeError, ValueError) as exc:
        raise LevelConfigError(f"{key} must be a number, got {raw!r}") from exc
    if value < 0:
        raise LevelConfigError(f"{key} must not be negative, got {value}")
    return value
