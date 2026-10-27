import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for path in (REPO / "tools", REPO / "code"):
    if str(path) not in sys.path:
        sys.path.append(str(path))

from studio.campaign import Campaign
from studio.level_service import LevelService
from studio.tmx_io import TmxDocument


class LevelServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        maps, circuits = tmp / "fases", tmp / "circuitos"
        shutil.copytree(REPO / "assets" / "maps" / "fases", maps)
        shutil.copytree(REPO / "code" / "circuitos" / "generic_levels_4", circuits / "generic_levels_4")
        self.circuits = circuits / "generic_levels_4" / "fase_4"
        self.maps = maps
        self.service = LevelService(Campaign(maps, circuits))

    def tearDown(self):
        self._tmp.cleanup()

    def _panel(self, report, panel_id):
        return next(panel for panel in report["panels"] if panel["id"] == panel_id)

    def _edit_solution(self, panel_id, change):
        path = self.circuits / f"pannel{panel_id}_solution.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        change(payload["elements"])
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _set_panel_property(self, panel_id, name, value):
        tmx = self.maps / "generic_levels_4" / "fase_4.tmx"
        document = TmxDocument(tmx)
        data = document.to_dict()
        for group in data["objectgroups"]:
            for obj in group["objects"]:
                props = {prop["name"]: prop for prop in obj["properties"]}
                if obj.get("name") == "control_pannel" and props["pannel_id"]["value"] == str(panel_id):
                    props[name]["value"] = value
        document.update(data)
        document.save()

    def test_shipped_stage_4_level_passes_the_checklist(self):
        report = self.service.check("fase_4")

        self.assertEqual([panel["problems"] for panel in report["panels"]], [[], [], [], []])
        self.assertEqual(report["problems"], [])

    def test_expected_answer_shows_the_equivalent_resistance_for_stage_4(self):
        panel = self._panel(self.service.check("fase_4"), 1)

        self.assertIn("resistance", panel["expected"])

    def test_missing_ground_is_explained_in_plain_words(self):
        self._edit_solution(1, lambda elements: elements.__setitem__(
            slice(None), [e for e in elements if e["kind"] != "ground"]))

        problems = self._panel(self.service.check("fase_4"), 1)["problems"]

        self.assertTrue(any("terra" in problem for problem in problems), problems)

    def test_missing_problem_file_is_reported(self):
        (self.circuits / "pannel2.json").unlink()

        problems = self._panel(self.service.check("fase_4"), 2)["problems"]

        self.assertTrue(any("pannel2.json" in problem for problem in problems), problems)

    def test_answer_type_from_another_stage_is_reported(self):
        self._set_panel_property(3, "type_solution", "power")

        problems = self._panel(self.service.check("fase_4"), 3)["problems"]

        self.assertTrue(any("power" in problem for problem in problems), problems)

    def test_target_component_missing_from_the_solution_is_reported(self):
        self._set_panel_property(1, "target_component", "R9")

        problems = self._panel(self.service.check("fase_4"), 1)["problems"]

        self.assertTrue(any("R9" in problem for problem in problems), problems)

    def test_solve_returns_values_per_resistor_for_an_unsaved_circuit(self):
        payload = json.loads((self.circuits / "pannel1_solution.json").read_text(encoding="utf-8"))

        result = self.service.solve(payload)

        self.assertIsNone(result["error"])
        self.assertEqual(set(result["resistors"]), {"R1", "R2", "R3"})
        self.assertGreater(result["totals"]["resistance"]["value"], 0)

    def test_solve_reports_invalid_values_instead_of_raising(self):
        payload = json.loads((self.circuits / "pannel1_solution.json").read_text(encoding="utf-8"))
        next(e for e in payload["elements"] if e.get("name") == "R1")["value"] = "abc"

        result = self.service.solve(payload)

        self.assertIn("abc", result["error"])

    def test_saved_circuit_is_written_in_the_game_format(self):
        payload = json.loads((self.circuits / "pannel1.json").read_text(encoding="utf-8"))

        self.service.save_circuit("fase_4", "pannel1", payload)

        saved = json.loads((self.circuits / "pannel1.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], 2)

    def test_circuit_names_outside_the_level_are_rejected(self):
        with self.assertRaises(ValueError):
            self.service.load_circuit("fase_4", "../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
