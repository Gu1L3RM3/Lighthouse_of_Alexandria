from __future__ import annotations

from pathlib import Path

from core.circuit_tools.circuit_domain import ElementKind
from core.circuit_tools.circuit_topology import CircuitGraph


class SpiceNetlistExporter:
    PREFIX = {
        ElementKind.RESISTOR: "R",
        ElementKind.VOLTAGE_SOURCE: "V",
        ElementKind.CURRENT_SOURCE: "I",
    }

    def render(self, graph: CircuitGraph) -> str:
        lines = ["* Alexandria DC circuit"]
        for branch in graph.branches:
            positive = "0" if branch.positive_node == 0 else f"N{branch.positive_node:03d}"
            negative = "0" if branch.negative_node == 0 else f"N{branch.negative_node:03d}"
            lines.append(f"{branch.name} {positive} {negative} {branch.value:.12g}")
        lines.extend(["", ".end"])
        return "\n".join(lines) + "\n"

    def write(self, graph: CircuitGraph, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.render(graph), encoding="utf-8", newline="\n")
