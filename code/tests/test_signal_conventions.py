import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from core.circuit_tools.solve_circuit import CircuitSolver
from core.settings import CELL_SIZE


class CircuitSignConventionsTest(unittest.TestCase):
    def _solve_netlist(self, netlist_content: str):
        fd, temp_path = tempfile.mkstemp(suffix=".net")
        os.close(fd)
        try:
            Path(temp_path).write_text(netlist_content, encoding="utf-8")
            solver = CircuitSolver(temp_path)
            self.assertTrue(solver.is_solved, f"Solver falhou para netlist:\n{netlist_content}")
            return solver
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def test_voltage_sources_opposing_and_aiding(self):
        opposing = "\n".join(
            [
                "R1 1 0 1k",
                "V2 2 1 20",
                "V1 2 0 15",
                "",
            ]
        )
        solver = self._solve_netlist(opposing)
        r1 = solver.get_resistor_results()["R1"]
        self.assertAlmostEqual(float(r1["voltage"]["value"]), -5.0, places=6)
        self.assertAlmostEqual(float(r1["current"]["value"]), -0.005, places=9)

        aiding = "\n".join(
            [
                "R1 1 0 1k",
                "V2 1 2 20",
                "V1 2 0 15",
                "",
            ]
        )
        solver = self._solve_netlist(aiding)
        r1 = solver.get_resistor_results()["R1"]
        self.assertAlmostEqual(float(r1["voltage"]["value"]), 35.0, places=6)
        self.assertAlmostEqual(float(r1["current"]["value"]), 0.035, places=9)

    def test_current_source_direction(self):
        downwards = "\n".join(
            [
                "I1 1 0 20",
                "R1 1 0 120k",
                "",
            ]
        )
        solver = self._solve_netlist(downwards)
        r1 = solver.get_resistor_results()["R1"]
        self.assertAlmostEqual(float(r1["voltage"]["value"]), -2_400_000.0, places=3)
        self.assertAlmostEqual(float(r1["current"]["value"]), -20.0, places=6)

        upwards = "\n".join(
            [
                "I1 0 1 20",
                "R1 1 0 120k",
                "",
            ]
        )
        solver = self._solve_netlist(upwards)
        r1 = solver.get_resistor_results()["R1"]
        self.assertAlmostEqual(float(r1["voltage"]["value"]), 2_400_000.0, places=3)
        self.assertAlmostEqual(float(r1["current"]["value"]), 20.0, places=6)


class LtSpiceTerminalsOrientationTest(unittest.TestCase):
    def setUp(self):
        fd_json, self.json_path = tempfile.mkstemp(suffix=".json")
        fd_net, self.net_path = tempfile.mkstemp(suffix=".net")
        fd_asc, self.asc_path = tempfile.mkstemp(suffix=".asc")
        os.close(fd_json)
        os.close(fd_net)
        os.close(fd_asc)
        Path(self.json_path).write_text("[]", encoding="utf-8")
        self.generator = LtSpiceGenerate(
            json_filepath=self.json_path,
            net_filepath=self.net_path,
            lt_spice_filepath=self.asc_path,
            entity_manager=None,
        )

    def tearDown(self):
        for p in (self.json_path, self.net_path, self.asc_path):
            try:
                os.remove(p)
            except OSError:
                pass

    def _build_entity(self, entity_type: str, angle: int):
        return {
            "entity_type": entity_type,
            "components": [
                {"type": "Position", "x": 128, "y": 256},
                {"type": "Connectable", "connections": ["top", "bottom", "up", "down"]},
                {"type": "Sprite", "angle": angle},
            ],
        }

    def test_voltage_source_vertical_orientation(self):
        top = (128 + CELL_SIZE / 2, 256)
        bottom = (128 + CELL_SIZE / 2, 256 + 2 * CELL_SIZE)

        terms_90 = self.generator._get_terminals(self._build_entity("VoutageSource", 90))
        self.assertEqual(terms_90["pos"], top)
        self.assertEqual(terms_90["neg"], bottom)

        terms_270 = self.generator._get_terminals(self._build_entity("VoutageSource", 270))
        self.assertEqual(terms_270["pos"], bottom)
        self.assertEqual(terms_270["neg"], top)

    def test_current_source_vertical_orientation(self):
        top = (128 + CELL_SIZE / 2, 256)
        bottom = (128 + CELL_SIZE / 2, 256 + 2 * CELL_SIZE)

        terms_90 = self.generator._get_terminals(self._build_entity("CurrentSource", 90))
        self.assertEqual(terms_90["from"], bottom)
        self.assertEqual(terms_90["to"], top)

        terms_270 = self.generator._get_terminals(self._build_entity("CurrentSource", 270))
        self.assertEqual(terms_270["from"], top)
        self.assertEqual(terms_270["to"], bottom)


if __name__ == "__main__":
    unittest.main()
