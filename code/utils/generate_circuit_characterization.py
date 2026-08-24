from __future__ import annotations

import json
from pathlib import Path

from core.circuit_tools.circuit_domain import CircuitError, ElementKind
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.circuit_topology import CircuitGraphBuilder
from core.circuit_tools.numeric_solver import CircuitAnalysisService, DcMnaSolver
from core.settings import CELL_SIZE, CIRCUITOS_DIR


def characterize_circuits(root: Path = CIRCUITOS_DIR) -> dict:
    repository = CircuitJsonRepository()
    builder = CircuitGraphBuilder(CELL_SIZE)
    solver = DcMnaSolver()
    analysis = CircuitAnalysisService(solver)
    circuits: dict[str, dict] = {}

    for path in sorted(root.rglob("*.json")):
        if path.name == "eletric_storage.json":
            continue
        relative = path.relative_to(root).as_posix()
        document = repository.load(path)
        graph = builder.build(document)
        record = {
            "branches": [
                {
                    "name": branch.name,
                    "kind": branch.kind.value,
                    "positive_node": branch.positive_node,
                    "negative_node": branch.negative_node,
                    "value": branch.value,
                }
                for branch in graph.branches
            ],
            "node_count": graph.node_count,
            "has_ground": graph.has_ground,
        }
        try:
            solution = solver.solve(graph)
        except CircuitError as error:
            record["solution"] = {"error": type(error).__name__}
            circuits[relative] = record
            continue

        record["solution"] = {
            "nodes": {str(node): value for node, value in solution.node_voltages.items()},
            "components": {
                name: {
                    "voltage": result.voltage,
                    "current": result.current,
                    "power": result.power,
                }
                for name, result in solution.components.items()
            },
        }
        analyses: dict[str, dict] = {}
        for branch in graph.branches:
            if branch.kind is not ElementKind.RESISTOR:
                continue
            try:
                thevenin = analysis.thevenin(graph, branch.name)
                norton = analysis.norton(graph, branch.name)
                analyses[branch.name] = {
                    "thevenin_voltage": thevenin.voltage,
                    "thevenin_resistance": thevenin.resistance,
                    "norton_current": norton.current,
                    "norton_resistance": norton.resistance,
                }
            except CircuitError as error:
                analyses[branch.name] = {"error": type(error).__name__}
        record["analyses"] = analyses
        circuits[relative] = record

    return {"schema_version": 1, "circuits": circuits}


def write_fixture(output_path: Path, root: Path = CIRCUITOS_DIR) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(characterize_circuits(root), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "circuit_characterization_v2.json"
    write_fixture(destination)
    print(destination)
