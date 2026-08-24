import json
from pathlib import Path
import tempfile
import unittest

from core.circuit_tools.circuit_repository import CircuitJsonRepository
from utils.migrate_circuits_v2 import migrate_circuit_directory


class CircuitMigrationV2Tests(unittest.TestCase):
    def test_migrates_legacy_documents_and_skips_inventory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = [
                {
                    "entity_type": "Resistor",
                    "components": [
                        {"type": "Position", "x": 64, "y": 128},
                        {"type": "Sprite", "angle": 90},
                        {"type": "Dropped", "can_dropped": False},
                        {"type": "LabelComponent", "name": "R1", "value": "1k"},
                    ],
                }
            ]
            circuit_path = root / "panel.json"
            inventory_path = root / "eletric_storage.json"
            circuit_path.write_text(json.dumps(legacy), encoding="utf-8")
            inventory_path.write_text('{"Resistor": ["1k"]}', encoding="utf-8")

            migrated = migrate_circuit_directory(root)

            self.assertEqual(migrated, [circuit_path])
            payload = json.loads(circuit_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(payload["elements"][0]["name"], "R1")
            self.assertEqual(json.loads(inventory_path.read_text(encoding="utf-8")), {"Resistor": ["1k"]})
            self.assertEqual(CircuitJsonRepository().load(circuit_path).elements[0].rotation, 90)


if __name__ == "__main__":
    unittest.main()
