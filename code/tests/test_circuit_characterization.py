import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.circuit_domain import CircuitError, CircuitValidationError, ElementKind
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.circuit_topology import CircuitGraphBuilder
from core.circuit_tools.numeric_solver import DcMnaSolver
from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from core.circuit_tools.solve_circuit import CircuitSolver as LegacyCircuitSolver
from core.settings import CELL_SIZE


class TrackedCircuitCharacterizationTests(unittest.TestCase):
    def test_numeric_solver_matches_tracked_generated_netlists(self):
        repository = CircuitJsonRepository()
        builder = CircuitGraphBuilder(CELL_SIZE)
        solver = DcMnaSolver()
        circuit_root = ROOT / "circuitos"
        compared = 0

        for json_path in circuit_root.rglob("*.json"):
            if json_path.name == "eletric_storage.json":
                continue
            relative = json_path.relative_to(circuit_root)

            try:
                document = repository.load(json_path)
            except CircuitValidationError:
                self.assertIn(
                    relative.as_posix(),
                    {
                        "generic_levels_5/fase_5/pannel2.json",
                        "generic_levels_5/fase_5/pannel2_solution.json",
                    },
                )
                continue
            graph = builder.build(document)
            generator = LtSpiceGenerate(
                json_filepath=str(json_path),
                net_filepath="unused.net",
                lt_spice_filepath="unused.asc",
                entity_manager=None,
            )
            legacy_lines = generator.generate_netlist()
            with tempfile.TemporaryDirectory() as tmp:
                netlist_path = Path(tmp) / "generated.net"
                netlist_path.write_text("\n".join(legacy_lines) + "\n", encoding="utf-8")
                legacy = LegacyCircuitSolver(str(netlist_path))
            try:
                current = solver.solve(graph)
            except CircuitError:
                self.assertFalse(legacy.is_solved, str(relative))
                continue
            self.assertTrue(legacy.is_solved, str(relative))

            legacy_resistors = legacy.get_resistor_results()
            current_resistors = {
                branch.name: current.components[branch.name]
                for branch in graph.branches
                if branch.kind is ElementKind.RESISTOR
            }
            self.assertEqual(set(current_resistors), set(legacy_resistors), str(relative))
            for name, result in current_resistors.items():
                expected = legacy_resistors[name]
                self.assertAlmostEqual(
                    result.voltage,
                    float(expected["voltage"]["value"]),
                    delta=max(1e-10, abs(result.voltage) * 1e-8),
                    msg=f"{relative}: {name} voltage",
                )
                self.assertAlmostEqual(
                    result.current,
                    float(expected["current"]["value"]),
                    delta=max(1e-12, abs(result.current) * 1e-8),
                    msg=f"{relative}: {name} current",
                )
            compared += 1

        self.assertGreaterEqual(compared, 30)


if __name__ == "__main__":
    unittest.main()
