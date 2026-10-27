import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.web_storage_sync import WebStorageSync


class FakeLocalStorage:
    """Mirrors the browser localStorage surface pygbag exposes."""

    def __init__(self, items=None):
        self.items = dict(items or {})

    @property
    def length(self):
        return len(self.items)

    def key(self, index):
        return list(self.items)[index]

    def getItem(self, key):
        return self.items.get(key)

    def setItem(self, key, value):
        self.items[key] = value

    def removeItem(self, key):
        self.items.pop(key, None)


class WebStorageSyncTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.save_dir = self.root / "save"
        self.save_dir.mkdir()
        self.circuit_dir = self.root / "circuitos"
        self.circuit_dir.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _sync(self, storage):
        return WebStorageSync(self.root, [self.save_dir, self.circuit_dir], storage)

    def test_restore_writes_stored_files_into_data_dirs(self):
        storage = FakeLocalStorage({"alexandria:save/savegame.json": '{"a": 1}'})

        self._sync(storage).restore()

        self.assertEqual((self.save_dir / "savegame.json").read_text(encoding="utf-8"), '{"a": 1}')

    def test_restore_ignores_keys_from_other_apps(self):
        storage = FakeLocalStorage({"other:save/x.json": "{}"})

        self._sync(storage).restore()

        self.assertFalse((self.save_dir / "x.json").exists())

    def test_persist_changes_stores_only_files_written_after_restore(self):
        (self.circuit_dir / "bundled.json").write_text("{}", encoding="utf-8")
        storage = FakeLocalStorage()
        sync = self._sync(storage)
        sync.restore()

        (self.save_dir / "savegame.json").write_text('{"b": 2}', encoding="utf-8")
        sync.persist_changes()

        self.assertEqual(storage.items, {"alexandria:save/savegame.json": '{"b": 2}'})

    def test_persist_changes_removes_deleted_files_from_storage(self):
        storage = FakeLocalStorage({"alexandria:save/savegame.json": "{}"})
        sync = self._sync(storage)
        sync.restore()

        (self.save_dir / "savegame.json").unlink()
        sync.persist_changes()

        self.assertEqual(storage.items, {})


if __name__ == "__main__":
    unittest.main()
