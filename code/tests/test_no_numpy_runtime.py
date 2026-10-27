import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Runs in a fresh interpreter where `import numpy` raises ImportError, which is
# what the PyInstaller build sees because Alexandria.spec excludes numpy.
RUNTIME_WITHOUT_NUMPY = textwrap.dedent(
    """
    import importlib
    import pkgutil
    import sys

    sys.modules["numpy"] = None
    sys.path.insert(0, ".")

    import game  # entry-point import graph used by main.py
    import scenes
    for module in pkgutil.walk_packages(scenes.__path__, "scenes."):
        importlib.import_module(module.name)

    from pathfinding.core.grid import Grid
    from pathfinding.finder.a_star import AStarFinder
    grid = Grid(matrix=[[True, True], [False, True]])
    path, _ = AStarFinder().find_path(grid.node(0, 0), grid.node(1, 1), grid)
    assert [(node.x, node.y) for node in path] == [(0, 0), (1, 0), (1, 1)], path

    from core.circuit_tools.circuit_domain import ElementKind
    from core.circuit_tools.circuit_topology import CircuitBranch, CircuitGraph
    from core.circuit_tools.numeric_solver import DcMnaSolver
    circuit = CircuitGraph(
        (
            CircuitBranch("V1", ElementKind.VOLTAGE_SOURCE, 1, 0, 10),
            CircuitBranch("R1", ElementKind.RESISTOR, 1, 0, 1000),
        ),
        1,
        True,
    )
    assert abs(DcMnaSolver().solve(circuit).components["R1"].current - 0.01) < 1e-9
    """
)


class NoNumpyRuntimeTests(unittest.TestCase):
    def test_game_code_does_not_import_numpy(self):
        offenders = [
            str(path.relative_to(ROOT))
            for path in ROOT.rglob("*.py")
            if "tests" not in path.parts
            and any(
                line.strip().startswith(("import numpy", "from numpy"))
                for line in path.read_text(encoding="utf-8").splitlines()
            )
        ]
        self.assertEqual(offenders, [])

    def test_game_runs_with_numpy_unavailable(self):
        env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        result = subprocess.run(
            [sys.executable, "-c", RUNTIME_WITHOUT_NUMPY],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
