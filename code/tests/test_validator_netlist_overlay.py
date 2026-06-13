import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.serialization_manager import SerializationManager
from core.systems.circuit_validators.max_power_transfer_validator_system import MaxPowerTransferValidatorSystem
from core.systems.circuit_validators.thevenin_norton_validator_system import TheveninNortonValidatorSystem


class ValidatorNetlistOverlayTest(unittest.TestCase):
    def test_thevenin_validator_detects_overlay_component(self):
        fd, temp_path = tempfile.mkstemp(suffix=".net")
        os.close(fd)
        try:
            Path(temp_path).write_text("R1 1 0 1k\nV1 1 0 10\n", encoding="utf-8")
            validator = TheveninNortonValidatorSystem("generic_levels_6/fase_6")
            self.assertTrue(validator._net_has_component(temp_path, "R1"))
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def test_max_power_validator_reads_resistor_value_from_overlay(self):
        fd, temp_path = tempfile.mkstemp(suffix=".net")
        os.close(fd)
        try:
            Path(temp_path).write_text("R1 1 0 1k\nV1 1 0 10\n", encoding="utf-8")
            SerializationManager.update_component_value(temp_path, "R1", "2k")
            validator = MaxPowerTransferValidatorSystem("generic_levels_7/fase_7")
            label, value = validator._read_component_value_from_netlist(temp_path, "R1")
            self.assertEqual(label, "2k")
            self.assertEqual(value, 2000.0)
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
