from __future__ import annotations

from core.circuit_tools.circuit_domain import ElementKind
from core.circuit_tools.circuit_topology import CircuitGraph
from core.circuit_tools.numeric_solver import CircuitSolution
from utils.setter_values import SetterValues


def _quantity(value: float, unit: str) -> dict[str, object]:
    return {"label": SetterValues.format_eng(float(value), unit), "value": float(value)}


class CircuitResultAdapter:
    def resistor_results(self, graph: CircuitGraph, solution: CircuitSolution) -> dict[str, dict]:
        results: dict[str, dict] = {}
        for branch in graph.branches:
            if branch.kind is not ElementKind.RESISTOR:
                continue
            result = solution.components[branch.name]
            results[branch.name] = {
                "voltage": _quantity(result.voltage, "V"),
                "current": _quantity(result.current, "A"),
                "power": _quantity(result.power, "W"),
            }
        return results

    def total_values(self, graph: CircuitGraph, solution: CircuitSolution) -> dict | None:
        sources = [branch for branch in graph.branches if branch.kind is ElementKind.VOLTAGE_SOURCE]
        if not sources:
            sources = [branch for branch in graph.branches if branch.kind is ElementKind.CURRENT_SOURCE]
        if not sources:
            return None
        result = solution.components[sources[0].name]
        if abs(result.current) < 1e-12:
            return None
        voltage = float(result.voltage)
        current = float(result.current)
        return {
            "voltage": _quantity(voltage, "V"),
            "current": _quantity(current, "A"),
            "power": _quantity(abs(voltage * current), "W"),
            "resistance": _quantity(abs(voltage / current), ""),
        }
