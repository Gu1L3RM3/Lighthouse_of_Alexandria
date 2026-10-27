import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.linear_system import SingularMatrixError, solve_linear_system


class LinearSystemTests(unittest.TestCase):
    def test_solves_two_by_two_system(self):
        # 2x + y = 5, x - y = 1  ->  x = 2, y = 1
        values = solve_linear_system([[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0])
        self.assertAlmostEqual(values[0], 2.0)
        self.assertAlmostEqual(values[1], 1.0)

    def test_pivots_when_leading_coefficient_is_zero(self):
        # MNA matrices often start with a zero on the diagonal.
        values = solve_linear_system([[0.0, 1.0], [1.0, 0.0]], [3.0, 4.0])
        self.assertAlmostEqual(values[0], 4.0)
        self.assertAlmostEqual(values[1], 3.0)

    def test_solves_three_by_three_system(self):
        matrix = [[3.0, 2.0, -1.0], [2.0, -2.0, 4.0], [-1.0, 0.5, -1.0]]
        values = solve_linear_system(matrix, [1.0, -2.0, 0.0])
        for actual, expected in zip(values, (1.0, -2.0, -2.0)):
            self.assertAlmostEqual(actual, expected)

    def test_singular_matrix_raises(self):
        with self.assertRaises(SingularMatrixError):
            solve_linear_system([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_does_not_mutate_inputs(self):
        matrix = [[2.0, 1.0], [1.0, -1.0]]
        rhs = [5.0, 1.0]
        solve_linear_system(matrix, rhs)
        self.assertEqual(matrix, [[2.0, 1.0], [1.0, -1.0]])
        self.assertEqual(rhs, [5.0, 1.0])


class NoNumpyDependencyTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
