import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.telemetry import NullTransport, WebBridgeTransport
from core.telemetry.browser import (
    create_transport,
    read_storage_prefix,
    read_viewport_size,
    read_visibility_state,
)
from core.web_storage_sync import KEY_PREFIX, WebStorageSync
from test_web_storage_sync import FakeLocalStorage


class FakeBridge:
    def __init__(self):
        self.pushed = []

    def push(self, payload):
        self.pushed.append(payload)


class FakeDocument:
    visibilityState = "hidden"


class FakeWindow:
    """Only what the page defines exists, like a browser `window`."""

    def __init__(self, **attributes):
        for name, value in attributes.items():
            setattr(self, name, value)


class ThrowingWindow:
    def __getattr__(self, name):
        raise RuntimeError("JS proxy failure")


class TransportFactoryTest(unittest.TestCase):
    def test_desktop_gets_null_transport_even_with_a_bridge(self):
        window = FakeWindow(alexTelemetry=FakeBridge())

        self.assertIsInstance(create_transport("linux", window), NullTransport)

    def test_web_without_bridge_gets_null_transport(self):
        self.assertIsInstance(create_transport("emscripten", FakeWindow()), NullTransport)

    def test_web_with_null_bridge_gets_null_transport(self):
        self.assertIsInstance(create_transport("emscripten", FakeWindow(alexTelemetry=None)), NullTransport)

    def test_web_with_bridge_gets_web_bridge_transport(self):
        window = FakeWindow(alexTelemetry=FakeBridge())

        self.assertIsInstance(create_transport("emscripten", window), WebBridgeTransport)

    def test_web_bridge_transport_pushes_payload_to_the_bridge(self):
        bridge = FakeBridge()

        WebBridgeTransport(FakeWindow(alexTelemetry=bridge)).send("[]")

        self.assertEqual(bridge.pushed, ["[]"])

    def test_window_errors_fall_back_to_null_transport(self):
        self.assertIsInstance(create_transport("emscripten", ThrowingWindow()), NullTransport)


class BrowserReadersTest(unittest.TestCase):
    def test_storage_prefix_defaults_without_page_setting(self):
        self.assertEqual(read_storage_prefix(FakeWindow()), KEY_PREFIX)

    def test_storage_prefix_uses_page_setting(self):
        window = FakeWindow(ALEX_STORAGE_PREFIX="study:p42:")

        self.assertEqual(read_storage_prefix(window), "study:p42:")

    def test_storage_prefix_ignores_non_string_setting(self):
        self.assertEqual(read_storage_prefix(FakeWindow(ALEX_STORAGE_PREFIX=42)), KEY_PREFIX)

    def test_visibility_state_reads_document(self):
        self.assertEqual(read_visibility_state(FakeWindow(document=FakeDocument())), "hidden")

    def test_visibility_state_is_none_when_unreadable(self):
        self.assertIsNone(read_visibility_state(ThrowingWindow()))

    def test_viewport_size_reads_inner_size(self):
        window = FakeWindow(innerWidth=1366, innerHeight=768)

        self.assertEqual(read_viewport_size(window), (1366, 768))

    def test_viewport_size_is_none_when_unreadable(self):
        self.assertIsNone(read_viewport_size(ThrowingWindow()))


class StoragePrefixSyncTest(unittest.TestCase):
    def test_custom_prefix_separates_saves_of_students_sharing_a_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_dir = root / "save"
            save_dir.mkdir()
            storage = FakeLocalStorage({"alexandria:save/savegame.json": '{"other": 1}'})
            sync = WebStorageSync(root, [save_dir], storage, key_prefix="study:p42:")
            sync.restore()

            (save_dir / "savegame.json").write_text('{"mine": 1}', encoding="utf-8")
            sync.persist_changes()

            self.assertEqual(storage.items["study:p42:save/savegame.json"], '{"mine": 1}')
            self.assertEqual(storage.items["alexandria:save/savegame.json"], '{"other": 1}')

    def test_custom_prefix_restores_only_its_own_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_dir = root / "save"
            save_dir.mkdir()
            storage = FakeLocalStorage({"alexandria:save/savegame.json": '{"other": 1}'})

            WebStorageSync(root, [save_dir], storage, key_prefix="study:p42:").restore()

            self.assertFalse((save_dir / "savegame.json").exists())


if __name__ == "__main__":
    unittest.main()
