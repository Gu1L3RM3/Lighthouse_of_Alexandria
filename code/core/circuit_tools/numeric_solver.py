from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from core.circuit_tools.circuit_domain import CircuitError, ElementKind
from core.circuit_tools.circuit_topology import CircuitBranch, CircuitGraph


class CircuitSolveError(CircuitError):
    pass


class SingularCircuitError(CircuitSolveError):
    pass


class MissingGroundError(CircuitSolveError):
    pass


@dataclass(frozen=True, slots=True)
class ComponentResult:
    voltage: float
    current: float
    power: float


@dataclass(frozen=True, slots=True)
class CircuitSolution:
    node_voltages: dict[int, float]
    components: dict[str, ComponentResult]

    def voltage_at(self, node: int) -> float:
        return 0.0 if node == 0 else self.node_voltages[node]


@dataclass(frozen=True, slots=True)
class TheveninResult:
    voltage: float
    resistance: float
    positive_node: int
    negative_node: int


@dataclass(frozen=True, slots=True)
class NortonResult:
    current: float
    resistance: float
    positive_node: int
    negative_node: int


class DcMnaSolver:
    def solve(self, graph: CircuitGraph) -> CircuitSolution:
        if not graph.has_ground:
            raise MissingGroundError("Circuit requires a ground reference")
        voltage_sources = tuple(
            branch for branch in graph.branches if branch.kind is ElementKind.VOLTAGE_SOURCE
        )
        size = graph.node_count + len(voltage_sources)
        if size == 0:
            raise SingularCircuitError("Circuit has no solvable branches")
        matrix = np.zeros((size, size), dtype=float)
        rhs = np.zeros(size, dtype=float)
        voltage_index = {branch.name.casefold(): index for index, branch in enumerate(voltage_sources)}

        for branch in graph.branches:
            p = branch.positive_node
            n = branch.negative_node
            if branch.kind is ElementKind.RESISTOR:
                conductance = 1.0 / branch.value
                if p:
                    matrix[p - 1, p - 1] += conductance
                if n:
                    matrix[n - 1, n - 1] += conductance
                if p and n:
                    matrix[p - 1, n - 1] -= conductance
                    matrix[n - 1, p - 1] -= conductance
            elif branch.kind is ElementKind.CURRENT_SOURCE:
                if p:
                    rhs[p - 1] -= branch.value
                if n:
                    rhs[n - 1] += branch.value
            elif branch.kind is ElementKind.VOLTAGE_SOURCE:
                source_index = graph.node_count + voltage_index[branch.name.casefold()]
                if p:
                    matrix[p - 1, source_index] += 1.0
                    matrix[source_index, p - 1] += 1.0
                if n:
                    matrix[n - 1, source_index] -= 1.0
                    matrix[source_index, n - 1] -= 1.0
                rhs[source_index] = branch.value

        try:
            values = np.linalg.solve(matrix, rhs)
        except np.linalg.LinAlgError as exc:
            raise SingularCircuitError("Circuit does not have a unique DC solution") from exc

        node_voltages = {node: float(values[node - 1]) for node in range(1, graph.node_count + 1)}
        components: dict[str, ComponentResult] = {}
        for branch in graph.branches:
            p_voltage = 0.0 if branch.positive_node == 0 else node_voltages[branch.positive_node]
            n_voltage = 0.0 if branch.negative_node == 0 else node_voltages[branch.negative_node]
            voltage = p_voltage - n_voltage
            if branch.kind is ElementKind.RESISTOR:
                current = voltage / branch.value
            elif branch.kind is ElementKind.CURRENT_SOURCE:
                current = branch.value
            else:
                source_index = graph.node_count + voltage_index[branch.name.casefold()]
                current = float(values[source_index])
            components[branch.name] = ComponentResult(voltage, current, voltage * current)
        return CircuitSolution(node_voltages, components)


class CircuitAnalysisService:
    TEST_SOURCE_NAME = "VTEST_ANALYSIS"

    def __init__(self, solver: DcMnaSolver | None = None):
        self.solver = solver or DcMnaSolver()

    def thevenin(self, graph: CircuitGraph, component_name: str) -> TheveninResult:
        target = graph.branch(component_name)
        open_graph = graph.without(component_name)
        open_solution = self.solver.solve(open_graph)
        vth = open_solution.voltage_at(target.positive_node) - open_solution.voltage_at(target.negative_node)

        passive_branches: list[CircuitBranch] = []
        for branch in open_graph.branches:
            if branch.kind is ElementKind.CURRENT_SOURCE:
                continue
            if branch.kind is ElementKind.VOLTAGE_SOURCE:
                passive_branches.append(
                    CircuitBranch(branch.name, branch.kind, branch.positive_node, branch.negative_node, 0.0)
                )
            else:
                passive_branches.append(branch)
        passive_branches.append(
            CircuitBranch(
                self.TEST_SOURCE_NAME,
                ElementKind.VOLTAGE_SOURCE,
                target.positive_node,
                target.negative_node,
                1.0,
            )
        )
        test_solution = self.solver.solve(
            CircuitGraph(tuple(passive_branches), graph.node_count, graph.has_ground)
        )
        test_current = test_solution.components[self.TEST_SOURCE_NAME].current
        if math.isclose(test_current, 0.0, abs_tol=1e-15):
            raise SingularCircuitError("Thevenin resistance is infinite")
        return TheveninResult(
            voltage=float(vth),
            resistance=abs(1.0 / test_current),
            positive_node=target.positive_node,
            negative_node=target.negative_node,
        )

    def norton(self, graph: CircuitGraph, component_name: str) -> NortonResult:
        thevenin = self.thevenin(graph, component_name)
        return NortonResult(
            current=thevenin.voltage / thevenin.resistance,
            resistance=thevenin.resistance,
            positive_node=thevenin.positive_node,
            negative_node=thevenin.negative_node,
        )
