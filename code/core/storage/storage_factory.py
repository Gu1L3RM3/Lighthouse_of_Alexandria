from __future__ import annotations

from core.storage.json_document_storage import (
    BrowserJsonDocumentStorage,
    JsonDocumentStorage,
)


class StorageFactory:
    SAVE_KEY = "alexandria.savegame"
    PREFERENCES_KEY = "alexandria.preferences"

    @classmethod
    def for_save(cls) -> JsonDocumentStorage:
        return BrowserJsonDocumentStorage(cls.SAVE_KEY)

    @classmethod
    def for_preferences(cls) -> JsonDocumentStorage:
        return BrowserJsonDocumentStorage(cls.PREFERENCES_KEY)
