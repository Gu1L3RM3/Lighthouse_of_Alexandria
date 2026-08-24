import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.circuit_domain import (
    CircuitDocument,
    CircuitElement,
    CircuitValidationError,
    ElementKind,
    parse_engineering_value,
)
from core.circuit_tools.circuit_repository import CircuitJsonRepository


class EngineeringValueTests(unittest.TestCase):
    def test_parses_supported_suffixes(self):
        expected = {
            "2p": 2e-12,
            "3n": 3e-9,
            "4u": 4e-6,
            "5m": 5e-3,
            "6k": 6e3,
            "7meg": 7e6,
            "8g": 8e9,
            "9t": 9e12,
            "-1.5K": -1500.0,
        }
        for raw, value in expected.items():
            with self.subTest(raw=raw):
                self.assertAlmostEqual(parse_engineering_value(raw), value)


class CircuitDocumentTests(unittest.TestCase):
    def test_rejects_duplicate_component_names(self):
        element = CircuitElement(ElementKind.RESISTOR, 0, 0, name="R1", value="1k")
        with self.assertRaises(CircuitValidationError):
            CircuitDocument(elements=(element, element))

    def test_with_component_value_returns_new_document(self):
        original = CircuitDocument(
            elements=(CircuitElement(ElementKind.RESISTOR, 0, 0, name="R1", value="1k"),)
        )
        changed = original.with_component_value("R1", "2k")
        self.assertEqual(original.elements[0].value, "1k")
        self.assertEqual(changed.elements[0].value, "2k")


class CircuitRepositoryTests(unittest.TestCase):
    def test_migrates_legacy_voutage_source(self):
        legacy = [
            {
                "entity_type": "VoutageSource",
                "components": [
                    {"type": "Position", "x": 128, "y": 256},
                    {"type": "Sprite", "angle": 90, "image_path": "ignored.png"},
                    {"type": "LabelComponent", "name": "V1", "value": "12", "font_path": "ignored.ttf"},
                    {"type": "Connectable", "connections": ["top", "bottom"]},
                    {"type": "Dropped", "can_dropped": False},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.json"
            path.write_text(json.dumps(legacy), encoding="utf-8")
            document = CircuitJsonRepository().load(path)

        self.assertEqual(document.schema_version, 2)
        self.assertEqual(document.elements[0].kind, ElementKind.VOLTAGE_SOURCE)
        self.assertEqual(document.elements[0].rotation, 90)
        self.assertFalse(document.elements[0].editable)

    def test_v2_round_trip_omits_rendering_state(self):
        document = CircuitDocument(
            elements=(
                CircuitElement(ElementKind.RESISTOR, 64, 128, 90, True, "R1", "2.2k"),
                CircuitElement(ElementKind.GROUND, 64, 256, 0, False),
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "circuit.json"
            repository = CircuitJsonRepository()
            repository.save(path, document)
            payload = json.loads(path.read_text(encoding="utf-8"))
            loaded = repository.load(path)

        self.assertEqual(loaded, document)
        self.assertEqual(payload["schema_version"], 2)
        self.assertNotIn("Sprite", json.dumps(payload))
        self.assertNotIn("Connectable", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
