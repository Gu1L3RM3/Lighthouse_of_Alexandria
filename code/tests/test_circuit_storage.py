import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.serialization_manager import SerializationManager
from core.storage.json_value_storage import InMemoryJsonValueStorage


class SerializationManagerWebStorageTest(unittest.TestCase):
    def setUp(self):
        self.original_storage_builder = SerializationManager._storage_builder
        self.memory_store: dict[str, InMemoryJsonValueStorage] = {}

        def storage_builder(key: str):
            return self.memory_store.setdefault(key, InMemoryJsonValueStorage())

        SerializationManager._storage_builder = staticmethod(storage_builder)

    def tearDown(self):
        SerializationManager._storage_builder = self.original_storage_builder

    def test_save_and_load_eletric_storage_from_value_storage(self):
        payload = {"Resistor": {"1k": 2}}
        SerializationManager.save_eletric_storage(payload)
        self.assertEqual(SerializationManager.load_eletric_storage(), payload)

    def test_clear_eletric_storage_resets_to_empty_dict(self):
        SerializationManager.save_eletric_storage({"Node": {"n": 1}})
        SerializationManager.clear_eletric_storage()
        self.assertEqual(SerializationManager.load_eletric_storage(), {})

    def test_save_and_load_entities_uses_stable_circuit_key(self):
        SerializationManager.save_entities_to_json([], "fase_4/pannel_1.json")
        loaded = SerializationManager.load_entities_from_json("fase_4/pannel_1.json")
        self.assertEqual(loaded, [])

        expected_key = SerializationManager._circuit_storage_key("fase_4/pannel_1.json")
        self.assertIn(expected_key, self.memory_store)

    def test_load_entities_falls_back_to_bundled_panel_file(self):
        loaded = SerializationManager.load_entities_data("generic_levels_3/fase_3/pannel1.json")
        self.assertGreater(len(loaded), 0)
