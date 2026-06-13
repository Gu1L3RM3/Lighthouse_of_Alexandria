import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.repositories.language_preferences_repository import LanguagePreferencesRepository
from core.managers.save_game_manager import SaveGameManager
from core.storage.json_document_storage import (
    BrowserJsonDocumentStorage,
    FileJsonDocumentStorage,
    InMemoryJsonDocumentStorage,
)
from core.storage.storage_factory import StorageFactory


class FileJsonDocumentStorageTest(unittest.TestCase):
    def test_save_load_exists_and_clear_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "save" / "payload.json"
            storage = FileJsonDocumentStorage(path)

            self.assertFalse(storage.exists())
            storage.save({"value": 10})
            self.assertTrue(storage.exists())
            self.assertEqual(storage.load(), {"value": 10})

            storage.clear()
            self.assertFalse(storage.exists())
            self.assertIsNone(storage.load())


class BrowserJsonDocumentStorageTest(unittest.TestCase):
    def test_bridge_uses_local_storage_like_adapter(self):
        class _FakeStorageAdapter:
            def __init__(self):
                self.data = {}

            def getItem(self, key):
                return self.data.get(key)

            def setItem(self, key, value):
                self.data[key] = value

            def removeItem(self, key):
                self.data.pop(key, None)

        adapter = _FakeStorageAdapter()
        storage = BrowserJsonDocumentStorage("alex-save", storage_adapter=adapter)

        self.assertFalse(storage.exists())
        storage.save({"scene": "level_1"})
        self.assertTrue(storage.exists())
        self.assertEqual(storage.load(), {"scene": "level_1"})
        storage.clear()
        self.assertIsNone(storage.load())


class SaveGameManagerStorageIntegrationTest(unittest.TestCase):
    def test_manager_uses_injected_storage_contract(self):
        storage = InMemoryJsonDocumentStorage()
        manager = SaveGameManager(storage=storage)

        manager.save_game("level_1", current_lives=3, max_lives=10)
        data = manager.load_game()

        self.assertIsNotNone(data)
        self.assertEqual(data["current_scene"], "level_1")
        self.assertEqual(data["lives"]["current"], 3)
        self.assertTrue(manager.has_save())

    def test_manager_rejects_invalid_payload_from_storage(self):
        storage = InMemoryJsonDocumentStorage({"schema_version": 999})
        manager = SaveGameManager(storage=storage)
        self.assertIsNone(manager.load_game())


class StorageFactoryTest(unittest.TestCase):
    def test_factory_returns_browser_storage_for_save(self):
        storage = StorageFactory.for_save()
        self.assertIsInstance(storage, BrowserJsonDocumentStorage)

    def test_factory_returns_browser_storage_for_preferences(self):
        storage = StorageFactory.for_preferences()
        self.assertIsInstance(storage, BrowserJsonDocumentStorage)


class LanguagePreferencesRepositoryStorageIntegrationTest(unittest.TestCase):
    def test_repository_uses_injected_storage_contract(self):
        storage = InMemoryJsonDocumentStorage()
        repository = LanguagePreferencesRepository(storage=storage)

        self.assertEqual(repository.load_language(), "en")
        repository.save_language("pt-BR")
        self.assertEqual(repository.load_language(), "pt-BR")
