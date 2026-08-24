from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitElement, ElementKind


Point = tuple[int, int]
TerminalRef = tuple[int, str]


@dataclass(frozen=True, slots=True)
class CircuitBranch:
    name: str
    kind: ElementKind
    positive_node: int
    negative_node: int
    value: float


@dataclass(frozen=True, slots=True)
class CircuitGraph:
    branches: tuple[CircuitBranch, ...]
    node_count: int
    has_ground: bool

    def branch(self, component_name: str) -> CircuitBranch:
        normalized = component_name.casefold()
        for branch in self.branches:
            if branch.name.casefold() == normalized:
                return branch
        raise KeyError(component_name)

    def without(self, component_name: str) -> CircuitGraph:
        normalized = component_name.casefold()
        branches = tuple(branch for branch in self.branches if branch.name.casefold() != normalized)
        if len(branches) == len(self.branches):
            raise KeyError(component_name)
        return CircuitGraph(branches, self.node_count, self.has_ground)


class _DisjointSet:
    def __init__(self, values: Iterable[TerminalRef]):
        self.parent = {value: value for value in values}

    def find(self, value: TerminalRef) -> TerminalRef:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: TerminalRef, right: TerminalRef) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


class CircuitGraphBuilder:
    def __init__(self, cell_size: int):
        self.cell_size = int(cell_size)

    def terminals_for(self, element: CircuitElement) -> dict[str, Point]:
        x, y = element.x, element.y
        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2
        angle = element.rotation

        if element.kind is ElementKind.NODE:
            return {
                "top": (center_x, y),
                "bottom": (center_x, y + self.cell_size),
                "left": (x, center_y),
                "right": (x + self.cell_size, center_y),
            }
        if element.kind is ElementKind.WIRE:
            if angle in {0, 180}:
                return {"left": (x, center_y), "right": (x + self.cell_size, center_y)}
            return {"top": (center_x, y), "bottom": (center_x, y + self.cell_size)}
        if element.kind is ElementKind.GROUND:
            return {"top": (center_x, y)}

        if angle in {0, 180}:
            left = (x, center_y)
            right = (x + 2 * self.cell_size, center_y)
            if element.kind is ElementKind.RESISTOR:
                return {"p1": left, "p2": right}
            if element.kind is ElementKind.VOLTAGE_SOURCE:
                return {"neg": left, "pos": right} if angle == 0 else {"pos": left, "neg": right}
            return {"from": left, "to": right} if angle == 0 else {"to": left, "from": right}

        top = (center_x, y)
        bottom = (center_x, y + 2 * self.cell_size)
        if element.kind is ElementKind.RESISTOR:
            return {"p1": top, "p2": bottom}
        if element.kind is ElementKind.VOLTAGE_SOURCE:
            return {"pos": top, "neg": bottom} if angle == 90 else {"neg": top, "pos": bottom}
        return {"to": top, "from": bottom} if angle == 90 else {"from": top, "to": bottom}

    def build(self, document: CircuitDocument) -> CircuitGraph:
        terminals = tuple(self.terminals_for(element) for element in document.elements)
        return self._build(document, terminals)

    def _build(
        self,
        document: CircuitDocument,
        terminals: tuple[dict[str, Point], ...],
    ) -> CircuitGraph:
        references = tuple(
            (index, name)
            for index, element_terminals in enumerate(terminals)
            for name in element_terminals
        )
        disjoint = _DisjointSet(references)
        by_position: dict[Point, list[TerminalRef]] = {}
        for index, element_terminals in enumerate(terminals):
            for name, point in element_terminals.items():
                by_position.setdefault(point, []).append((index, name))
        for refs in by_position.values():
            for ref in refs[1:]:
                disjoint.union(refs[0], ref)
        for index, element in enumerate(document.elements):
            if element.kind not in {ElementKind.NODE, ElementKind.WIRE}:
                continue
            refs = [(index, name) for name in terminals[index]]
            for ref in refs[1:]:
                disjoint.union(refs[0], ref)

        ground_roots = {
            disjoint.find((index, name))
            for index, element in enumerate(document.elements)
            if element.kind is ElementKind.GROUND
            for name in terminals[index]
        }
        electrical_refs = {
            (index, name)
            for index, element in enumerate(document.elements)
            if element.kind.is_electrical
            for name in terminals[index]
        }
        root_points: dict[TerminalRef, list[Point]] = {}
        for ref in electrical_refs:
            index, name = ref
            root_points.setdefault(disjoint.find(ref), []).append(terminals[index][name])
        non_ground_roots = sorted(
            (root for root in root_points if root not in ground_roots),
            key=lambda root: min((point[1], point[0]) for point in root_points[root]),
        )
        node_by_root = {root: index + 1 for index, root in enumerate(non_ground_roots)}
        for root in ground_roots:
            node_by_root[root] = 0

        branches: list[CircuitBranch] = []
        endpoint_names = {
            ElementKind.RESISTOR: ("p1", "p2"),
            ElementKind.VOLTAGE_SOURCE: ("pos", "neg"),
            ElementKind.CURRENT_SOURCE: ("from", "to"),
        }
        for index, element in enumerate(document.elements):
            if not element.kind.is_electrical:
                continue
            positive_name, negative_name = endpoint_names[element.kind]
            positive_root = disjoint.find((index, positive_name))
            negative_root = disjoint.find((index, negative_name))
            branches.append(
                CircuitBranch(
                    name=element.name or "",
                    kind=element.kind,
                    positive_node=node_by_root[positive_root],
                    negative_node=node_by_root[negative_root],
                    value=element.numeric_value,
                )
            )
        return CircuitGraph(tuple(branches), len(non_ground_roots), bool(ground_roots))


class CircuitTopologyIndex:
    """Incremental spatial index with independent topology/value revisions."""

    def __init__(self, cell_size: int, document: CircuitDocument | None = None):
        self.builder = CircuitGraphBuilder(cell_size)
        self._next_id = 1
        self._order: list[int] = []
        self._elements: dict[int, CircuitElement] = {}
        self._terminals: dict[int, dict[str, Point]] = {}
        self.by_position: dict[Point, set[TerminalRef]] = {}
        self.topology_revision = 0
        self.value_revision = 0
        self.last_affected_positions: frozenset[Point] = frozenset()
        for element in (document or CircuitDocument()).elements:
            self._insert(element)

    def _insert(self, element: CircuitElement) -> int:
        element_id = self._next_id
        self._next_id += 1
        terminals = self.builder.terminals_for(element)
        self._order.append(element_id)
        self._elements[element_id] = element
        self._terminals[element_id] = terminals
        for terminal_name, point in terminals.items():
            self.by_position.setdefault(point, set()).add((element_id, terminal_name))
        return element_id

    def add(self, element: CircuitElement) -> int:
        element_id = self._insert(element)
        self.topology_revision += 1
        self.last_affected_positions = frozenset(self._terminals[element_id].values())
        return element_id

    @property
    def element_ids(self) -> tuple[int, ...]:
        return tuple(self._order)

    def remove(self, element_id: int) -> CircuitElement:
        element = self._elements.pop(element_id)
        terminals = self._terminals.pop(element_id)
        self._order.remove(element_id)
        for terminal_name, point in terminals.items():
            refs = self.by_position[point]
            refs.discard((element_id, terminal_name))
            if not refs:
                del self.by_position[point]
        self.topology_revision += 1
        self.last_affected_positions = frozenset(terminals.values())
        return element

    def replace(self, element_id: int, element: CircuitElement) -> None:
        previous = self._elements[element_id]
        previous_terminals = self._terminals[element_id]
        previous_geometry = (previous.kind, previous.x, previous.y, previous.rotation)
        next_geometry = (element.kind, element.x, element.y, element.rotation)
        if previous_geometry == next_geometry:
            self._elements[element_id] = element
            if previous != element:
                self.value_revision += 1
            self.last_affected_positions = frozenset()
            return

        for terminal_name, point in previous_terminals.items():
            refs = self.by_position[point]
            refs.discard((element_id, terminal_name))
            if not refs:
                del self.by_position[point]
        next_terminals = self.builder.terminals_for(element)
        self._elements[element_id] = element
        self._terminals[element_id] = next_terminals
        for terminal_name, point in next_terminals.items():
            self.by_position.setdefault(point, set()).add((element_id, terminal_name))
        self.topology_revision += 1
        self.last_affected_positions = frozenset(
            (*previous_terminals.values(), *next_terminals.values())
        )

    def document(self) -> CircuitDocument:
        return CircuitDocument(tuple(self._elements[element_id] for element_id in self._order))

    def build(self) -> CircuitGraph:
        document = self.document()
        terminals = tuple(self._terminals[element_id] for element_id in self._order)
        return self.builder._build(document, terminals)
