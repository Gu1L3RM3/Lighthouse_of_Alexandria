import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.circuit_domain import ElementKind
from core.circuit_tools.circuit_topology import CircuitBranch, CircuitGraph
from core.circuit_tools.numeric_solver import CircuitAnalysisService, DcMnaSolver, SingularCircuitError


def graph(*branches: CircuitBranch) -> CircuitGraph:
    max_node = max((max(branch.positive_node, branch.negative_node) for branch in branches), default=0)
    return CircuitGraph(tuple(branches), max_node, True)


class NumericSolverTests(unittest.TestCase):
    def setUp(self):
        self.solver = DcMnaSolver()

    def test_voltage_sources_opposing_and_aiding(self):
        opposing = graph(
            CircuitBranch("R1", ElementKind.RESISTOR, 1, 0, 1000),
            CircuitBranch("V2", ElementKind.VOLTAGE_SOURCE, 2, 1, 20),
            CircuitBranch("V1", ElementKind.VOLTAGE_SOURCE, 2, 0, 15),
        )
        result = self.solver.solve(opposing).components["R1"]
        self.assertAlmostEqual(result.voltage, -5.0)
        self.assertAlmostEqual(result.current, -0.005)

        aiding = graph(
            CircuitBranch("R1", ElementKind.RESISTOR, 1, 0, 1000),
            CircuitBranch("V2", ElementKind.VOLTAGE_SOURCE, 1, 2, 20),
            CircuitBranch("V1", ElementKind.VOLTAGE_SOURCE, 2, 0, 15),
        )
        result = self.solver.solve(aiding).components["R1"]
        self.assertAlmostEqual(result.voltage, 35.0)
        self.assertAlmostEqual(result.current, 0.035)

    def test_current_source_direction(self):
        downward = graph(
            CircuitBranch("I1", ElementKind.CURRENT_SOURCE, 1, 0, 20),
            CircuitBranch("R1", ElementKind.RESISTOR, 1, 0, 120_000),
        )
        resistor = self.solver.solve(downward).components["R1"]
        self.assertAlmostEqual(resistor.voltage, -2_400_000)
        self.assertAlmostEqual(resistor.current, -20)

    def test_rejects_singular_circuit(self):
        floating = graph(CircuitBranch("R1", ElementKind.RESISTOR, 1, 2, 1000))
        with self.assertRaises(SingularCircuitError):
            self.solver.solve(floating)

    def test_thevenin_and_norton_are_computed_in_memory(self):
        circuit = graph(
            CircuitBranch("V1", ElementKind.VOLTAGE_SOURCE, 1, 0, 12),
            CircuitBranch("R1", ElementKind.RESISTOR, 1, 2, 1000),
            CircuitBranch("RLOAD", ElementKind.RESISTOR, 2, 0, 1000),
        )
        analysis = CircuitAnalysisService(self.solver)
        thevenin = analysis.thevenin(circuit, "RLOAD")
        norton = analysis.norton(circuit, "RLOAD")
        self.assertAlmostEqual(thevenin.voltage, 12.0)
        self.assertAlmostEqual(thevenin.resistance, 1000.0)
        self.assertAlmostEqual(norton.current, 0.012)


if __name__ == "__main__":
    unittest.main()
