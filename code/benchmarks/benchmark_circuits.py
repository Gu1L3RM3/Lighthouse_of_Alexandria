from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import core.circuit_tools

from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.circuit_topology import CircuitGraphBuilder
from core.circuit_tools.numeric_solver import DcMnaSolver
from core.settings import CELL_SIZE


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CIRCUIT = Path("final_fase/fase_8/pannel2_solution")


def _git_text(reference: str, relative_path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{reference}:{relative_path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )


def _median_seconds(callable_, samples: int) -> float:
    callable_()
    values = []
    gc.disable()
    try:
        for _ in range(samples):
            started = time.perf_counter()
            callable_()
            values.append(time.perf_counter() - started)
    finally:
        gc.enable()
    return statistics.median(values)


def benchmark(reference: str, circuit: Path = DEFAULT_CIRCUIT) -> dict[str, float]:
    json_relative = f"code/circuitos/{circuit.as_posix()}.json"
    net_relative = f"code/ltspice/{circuit.as_posix()}.net"
    legacy_json = _git_text(reference, json_relative)
    legacy_netlist = _git_text(reference, net_relative)

    repository = CircuitJsonRepository()
    current_path = ROOT / "code" / "circuitos" / f"{circuit.as_posix()}.json"
    document = repository.load(current_path)
    graph = CircuitGraphBuilder(CELL_SIZE).build(document)
    numeric_solver = DcMnaSolver()

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        legacy_module_root = temporary_root / "circuit_tools"
        legacy_module_root.mkdir()
        (legacy_module_root / "SMNA.py").write_text(
            _git_text(reference, "code/core/circuit_tools/SMNA.py"),
            encoding="utf-8",
        )
        legacy_solver_path = legacy_module_root / "solve_circuit.py"
        legacy_solver_path.write_text(
            _git_text(reference, "code/core/circuit_tools/solve_circuit.py"),
            encoding="utf-8",
        )
        netlist_path = temporary_root / "circuit.net"
        netlist_path.write_text(legacy_netlist, encoding="utf-8")
        legacy_json_path = temporary_root / "circuit.json"
        legacy_json_path.write_text(legacy_json, encoding="utf-8")

        core.circuit_tools.__path__.append(str(legacy_module_root))
        specification = importlib.util.spec_from_file_location("legacy_solve_circuit", legacy_solver_path)
        legacy_module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(legacy_module)
        old_solver_seconds = _median_seconds(
            lambda: legacy_module.CircuitSolver(netlist_path),
            samples=7,
        )
        old_load_seconds = _median_seconds(
            lambda: repository.load(legacy_json_path),
            samples=101,
        )

    new_solver_seconds = _median_seconds(lambda: numeric_solver.solve(graph), samples=101)
    new_load_seconds = _median_seconds(lambda: repository.load(current_path), samples=101)
    return {
        "old_solver_median_ms": old_solver_seconds * 1000,
        "new_solver_median_ms": new_solver_seconds * 1000,
        "solver_ratio": new_solver_seconds / old_solver_seconds,
        "old_load_median_ms": old_load_seconds * 1000,
        "new_load_median_ms": new_load_seconds * 1000,
        "load_ratio": new_load_seconds / old_load_seconds,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="61c96fd")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = benchmark(arguments.baseline_ref)
    rendered = json.dumps(result, indent=2) + "\n"
    if arguments.output:
        arguments.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if result["solver_ratio"] > 0.5 or result["load_ratio"] > 0.8:
        raise SystemExit("Circuit performance targets were not met")
