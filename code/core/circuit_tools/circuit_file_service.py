from __future__ import annotations

from pathlib import Path
from typing import Protocol

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitError, ElementKind
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.circuit_result_adapter import CircuitResultAdapter
from core.circuit_tools.circuit_topology import CircuitGraph, CircuitGraphBuilder
from core.circuit_tools.numeric_solver import CircuitAnalysisService, CircuitSolution, DcMnaSolver
from utils.setter_values import SetterValues


def _quantity(value: float, unit: str) -> dict[str, object]:
    return {"label": SetterValues.format_eng(float(value), unit), "value": float(value)}


class SolvedCircuit:
    def __init__(self, graph: CircuitGraph | None = None, solution: CircuitSolution | None = None):
        self.graph = graph
        self.solution = solution
        self.is_solved = graph is not None and solution is not None
        self._results = CircuitResultAdapter()
        self._analysis = CircuitAnalysisService()

    def get_resistor_results(self) -> dict:
        if not self.is_solved:
            return {}
        return self._results.resistor_results(self.graph, self.solution)

    def get_total_values(self) -> dict | None:
        if not self.is_solved:
            return None
        return self._results.total_values(self.graph, self.solution)

    def get_equivalent_resistance(self) -> float | None:
        totals = self.get_total_values()
        return float(totals["resistance"]["value"]) if totals else None

    def get_thevenin(self, component_name: str) -> dict | None:
        if not self.is_solved:
            return None
        try:
            result = self._analysis.thevenin(self.graph, component_name)
        except (CircuitError, KeyError):
            return None
        return {
            "component": component_name,
            "terminals": {"p_node": result.positive_node, "n_node": result.negative_node},
            "voltage": _quantity(result.voltage, "V"),
            "resistance": _quantity(result.resistance, ""),
        }

    def get_norton(self, component_name: str) -> dict | None:
        if not self.is_solved:
            return None
        try:
            result = self._analysis.norton(self.graph, component_name)
        except (CircuitError, KeyError):
            return None
        return {
            "component": component_name,
            "terminals": {"p_node": result.positive_node, "n_node": result.negative_node},
            "current": _quantity(result.current, "A"),
            "resistance": _quantity(result.resistance, ""),
        }


class CircuitService(Protocol):
    def load(self, path: str | Path) -> CircuitDocument: ...
    def save(self, path: str | Path, document: CircuitDocument) -> None: ...
    def save_component_value(self, path: str | Path, component_name: str, value: str) -> None: ...
    def remove_editable_elements(self, path: str | Path) -> None: ...
    def has_component(self, path: str | Path, component_name: str) -> bool: ...
    def resistor_names(self, path: str | Path) -> list[str]: ...
    def component_value(self, path: str | Path, component_name: str) -> tuple[str | None, float | None]: ...
    def component_nodes(self, path: str | Path) -> dict[str, tuple[str, str]]: ...
    def solve(self, path: str | Path) -> SolvedCircuit: ...

class CircuitFileService:
    """Application boundary for persisted circuit documents."""

    def __init__(self, cell_size: int):
        self.repository = CircuitJsonRepository()
        self.builder = CircuitGraphBuilder(cell_size)
        self.solver = DcMnaSolver()

    def load(self, path: str | Path) -> CircuitDocument:
        return self.repository.load(path)

    def save(self, path: str | Path, document: CircuitDocument) -> None:
        self.repository.save(path, document)

    def save_component_value(self, path: str | Path, component_name: str, value: str) -> None:
        document = self.load(path).with_component_value(component_name, str(value))
        self.save(path, document)

    def remove_editable_elements(self, path: str | Path) -> None:
        self.save(path, self.load(path).without_editable_elements())

    def has_component(self, path: str | Path, component_name: str) -> bool:
        normalized = component_name.casefold()
        return any(
            element.name and element.name.casefold() == normalized
            for element in self.load(path).elements
        )

    def resistor_names(self, path: str | Path) -> list[str]:
        return [
            element.name or ""
            for element in self.load(path).elements
            if element.kind is ElementKind.RESISTOR
        ]

    def component_value(self, path: str | Path, component_name: str) -> tuple[str | None, float | None]:
        normalized = component_name.casefold()
        for element in self.load(path).elements:
            if element.name and element.name.casefold() == normalized:
                return element.value, element.numeric_value
        return None, None

    def component_nodes(self, path: str | Path) -> dict[str, tuple[str, str]]:
        graph = self.builder.build(self.load(path))
        return {
            branch.name: (str(branch.positive_node), str(branch.negative_node))
            for branch in graph.branches
        }

    def solve(self, path: str | Path) -> SolvedCircuit:
        try:
            graph = self.builder.build(self.load(path))
            return SolvedCircuit(graph, self.solver.solve(graph))
        except (CircuitError, OSError, ValueError):
            return SolvedCircuit()
