import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.generate_circuit_characterization import characterize_circuits


class TrackedCircuitCharacterizationTests(unittest.TestCase):
    def assert_characterization_equal(self, actual, expected, path="root"):
        if isinstance(expected, float):
            self.assertTrue(
                math.isclose(float(actual), expected, rel_tol=1e-8, abs_tol=1e-10),
                f"{path}: {actual!r} != {expected!r}",
            )
            return
        if isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), path)
            for key in expected:
                self.assert_characterization_equal(actual[key], expected[key], f"{path}.{key}")
            return
        if isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), path)
            for index, item in enumerate(expected):
                self.assert_characterization_equal(actual[index], item, f"{path}[{index}]")
            return
        self.assertEqual(actual, expected, path)

    def test_tracked_circuits_match_characterized_results(self):
        fixture_path = ROOT / "tests" / "fixtures" / "circuit_characterization_v2.json"
        expected = json.loads(fixture_path.read_text(encoding="utf-8"))
        actual = characterize_circuits(ROOT / "circuitos")
        self.assert_characterization_equal(actual, expected)


if __name__ == "__main__":
    unittest.main()
