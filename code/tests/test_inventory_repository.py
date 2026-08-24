import json
from pathlib import Path
import tempfile
import unittest

from core.circuit_tools.inventory_repository import InventoryRepository


class InventoryRepositoryTests(unittest.TestCase):
    def test_load_migrates_legacy_voltage_source_key(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "inventory.json"
            path.write_text(
                json.dumps({"VoutageSource": {"5": 2}, "VoltageSource": {"5": 1, "9": 1}}),
                encoding="utf-8",
            )

            inventory = InventoryRepository(path).load()

            self.assertNotIn("VoutageSource", inventory)
            self.assertEqual(inventory["VoltageSource"], {"5": 3, "9": 1})

    def test_save_is_loadable_and_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "inventory.json"
            repository = InventoryRepository(path)
            repository.save({"Resistor": {"1k": 2}})

            self.assertEqual(repository.load(), {"Resistor": {"1k": 2}})
            self.assertEqual(list(path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
