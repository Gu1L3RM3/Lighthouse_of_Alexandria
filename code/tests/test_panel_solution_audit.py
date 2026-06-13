import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from core.circuit_tools.solve_circuit import CircuitSolver
from core.settings import CIRCUITOS_DIR


class PanelSolutionAuditTest(unittest.TestCase):
    def test_all_solution_json_panels_generate_solvable_netlists(self):
        circuit_root = Path(CIRCUITOS_DIR)
        solution_files = sorted(circuit_root.rglob("*_solution.json"))
        self.assertGreater(len(solution_files), 0)

        failures: list[str] = []
        for solution_file in solution_files:
            circuit_data = json.loads(solution_file.read_text(encoding="utf-8"))
            generator = LtSpiceGenerate.from_circuit_data(circuit_data=circuit_data, entity_manager=None)
            netlist_text = generator.build_netlist_text()
            solver = CircuitSolver.from_netlist_content(netlist_text)
            if not solver.is_solved:
                failures.append(str(solution_file.relative_to(circuit_root)))

        self.assertEqual(failures, [], f"Painéis de solução com falha: {failures}")

