from pathlib import Path

from core.settings import DEFAULT_LANGUAGE
from core.storage.json_document_storage import FileJsonDocumentStorage, JsonDocumentStorage
from core.storage.storage_factory import StorageFactory


class LanguagePreferencesRepository:
    SCHEMA_VERSION = 1

    def __init__(
        self,
        preferences_file: str | Path | None = None,
        storage: JsonDocumentStorage | None = None,
    ):
        if storage is not None:
            self.storage = storage
        elif preferences_file is not None:
            self.storage = FileJsonDocumentStorage(preferences_file)
        else:
            self.storage = StorageFactory.for_preferences()

    def load_language(self) -> str:
        data = self.storage.load()
        if not isinstance(data, dict):
            return DEFAULT_LANGUAGE
        if int(data.get("schema_version", -1)) != self.SCHEMA_VERSION:
            return DEFAULT_LANGUAGE

        language = data.get("language", DEFAULT_LANGUAGE)
        if not isinstance(language, str) or not language.strip():
            return DEFAULT_LANGUAGE
        return language

    def save_language(self, language: str) -> None:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "language": str(language),
        }
        self.storage.save(payload)
