import json
from datetime import datetime, timezone
from pathlib import Path

from core.settings import SAVE_FILE


class SaveGameManager:
    _instance = None
    SCHEMA_VERSION = 1
    _NON_PERSISTENT_SCENES = {
        "main_menu",
        "help",
        "credits",
        "death_transition",
        "ending_lighthouse",
        "ending_thanks_credits",
    }

    def __init__(self):
        self.save_file = Path(SAVE_FILE)
        self.save_file.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SaveGameManager()
        return cls._instance

    def should_persist_scene(self, scene_name: str | None) -> bool:
        if not scene_name:
            return False
        return scene_name not in self._NON_PERSISTENT_SCENES

    def has_save(self) -> bool:
        data = self.load_game()
        return data is not None

    def clear_save(self):
        try:
            self.save_file.unlink(missing_ok=True)
        except Exception:
            pass

    def autosave_scene(self, scene_name: str | None, current_lives: int, max_lives: int):
        if not self.should_persist_scene(scene_name):
            return
        self.save_game(scene_name, current_lives, max_lives)

    def save_game(self, scene_name: str, current_lives: int, max_lives: int):
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_scene": str(scene_name),
            "lives": {
                "current": int(current_lives),
                "max": int(max_lives),
            },
        }
        self._write_atomic(payload)

    def load_game(self) -> dict | None:
        if not self.save_file.exists():
            return None

        try:
            data = json.loads(self.save_file.read_text(encoding="utf-8"))
        except Exception:
            return None

        if not isinstance(data, dict):
            return None
        if int(data.get("schema_version", -1)) != self.SCHEMA_VERSION:
            return None

        scene_name = data.get("current_scene")
        lives = data.get("lives")
        if not isinstance(scene_name, str) or not scene_name:
            return None
        if not isinstance(lives, dict):
            return None

        current = lives.get("current")
        max_lives = lives.get("max")
        if not isinstance(current, int) or not isinstance(max_lives, int):
            return None
        if max_lives < 1:
            return None
        if current < 0:
            return None

        return data

    def _write_atomic(self, data: dict):
        tmp_file = self.save_file.with_suffix(self.save_file.suffix + ".tmp")
        try:
            tmp_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_file.replace(self.save_file)
        except Exception:
            pass

