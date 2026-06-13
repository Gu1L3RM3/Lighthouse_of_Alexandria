import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.serialization_manager import SerializationManager
from core.systems.circuit_validators.circuit_validator_system import CircuitValidatorSystem
from core.systems.circuit_validators.resistor_association_validator_system import ResistorAssotiationValidatorSystem


class RemainingValidatorOverlayTest(unittest.TestCase):
    def test_circuit_validator_lists_resistors_from_overlay(self):
        fd, temp_path = tempfile.mkstemp(suffix=".net")
        os.close(fd)
        try:
            Path(temp_path).write_text("R1 1 0 1k\nV1 1 0 10\n", encoding="utf-8")
            validator = CircuitValidatorSystem("generic_levels_3/fase_3")
            names = validator._list_resistor_names_in_netlist(temp_path)
            self.assertEqual(names, ["R1"])
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def test_resistor_association_randomizes_overlay_netlist(self):
        fd, temp_path = tempfile.mkstemp(suffix=".net")
        os.close(fd)
        try:
            Path(temp_path).write_text("R1 1 0 1k\nR2 1 0 2k\nV1 1 0 10\n", encoding="utf-8")
            validator = ResistorAssotiationValidatorSystem("generic_levels_4/fase_4")
            updates = validator._randomize_resistors_in_netlist(temp_path)
            self.assertEqual(set(updates.keys()), {"R1", "R2"})

            overlay_text = SerializationManager.load_netlist_text(temp_path)
            self.assertIsNotNone(overlay_text)
            self.assertIn("R1", overlay_text)
            self.assertIn("R2", overlay_text)
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

