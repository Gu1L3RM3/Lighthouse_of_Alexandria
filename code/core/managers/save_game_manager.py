from datetime import datetime, timezone

from core.storage.json_document_storage import JsonDocumentStorage
from core.storage.storage_factory import StorageFactory


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

    def __init__(self, storage: JsonDocumentStorage | None = None):
        self.storage = storage or StorageFactory.for_save()

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
        self.storage.clear()

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
        self.storage.save(payload)

    def load_game(self) -> dict | None:
        data = self.storage.load()
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
