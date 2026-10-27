import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.append(str(REPO / "tools"))

from studio.campaign import Campaign, CampaignError
from studio.tmx_io import TmxDocument


def _door_target(tmx: Path) -> str | None:
    for group in TmxDocument(tmx).to_dict()["objectgroups"]:
        if group["name"] == "door":
            for obj in group["objects"]:
                for prop in obj["properties"]:
                    if prop["name"] == "next_scene":
                        return prop["value"]
    return None


class CampaignTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.maps = tmp / "fases"
        self.circuits = tmp / "circuitos"
        shutil.copytree(REPO / "assets" / "maps" / "fases", self.maps)
        for folder in ("generic_levels_4", "generic_levels_7"):
            shutil.copytree(REPO / "code" / "circuitos" / folder, self.circuits / folder)
        self.campaign = Campaign(self.maps, self.circuits)

    def tearDown(self):
        self._tmp.cleanup()

    def _scenes(self):
        return [step["scene"] for step in self.campaign.chain()]

    def test_chain_follows_the_game_from_level_1_to_the_final_level(self):
        self.assertEqual(
            self._scenes(),
            ["level_1", "level_2", "exp_fase_3", "fase_3", "exp_fase_4", "fase_4", "exp_fase_5", "fase_5",
             "exp_fase_6", "fase_6", "exp_fase_7", "fase_7", "fase_8"],
        )

    def test_only_stage_levels_are_editable(self):
        editable = {step["scene"]: step["editable"] for step in self.campaign.chain()}

        self.assertTrue(editable["fase_4"])
        self.assertFalse(editable["exp_fase_4"])
        self.assertFalse(editable["level_1"])

    def test_inserting_after_a_level_rewires_the_doors_and_clones_its_circuits(self):
        self.campaign.insert_after("fase_4", "fase_4_2")

        self.assertEqual(self._scenes()[5:8], ["fase_4", "fase_4_2", "exp_fase_5"])
        self.assertEqual(_door_target(self.maps / "generic_levels_4" / "fase_4.tmx"), "fase_4_2")
        self.assertEqual(_door_target(self.maps / "generic_levels_4" / "fase_4_2.tmx"), "exp_fase_5")
        self.assertTrue((self.circuits / "generic_levels_4" / "fase_4_2" / "pannel1_solution.json").exists())

    def test_inserted_level_belongs_to_the_stage_of_the_level_before_it(self):
        self.campaign.insert_after("fase_7", "fase_7_2")

        stage = next(stage for stage in self.campaign.stages() if stage["number"] == 7)
        self.assertEqual(stage["levels"], ["fase_7", "fase_7_2"])
        self.assertEqual(_door_target(self.maps / "generic_levels_7" / "fase_7_2.tmx"), "fase_8")

    def test_blank_level_keeps_size_door_and_player_but_no_tiles_panels_or_circuits(self):
        self.campaign.insert_after("fase_4", "fase_4_2", blank=True)

        data = TmxDocument(self.maps / "generic_levels_4" / "fase_4_2.tmx").to_dict()
        names = {obj.get("name") for group in data["objectgroups"] for obj in group["objects"]}
        self.assertEqual((data["width"], data["height"]), (64, 64))
        self.assertTrue(all(not any(layer["data"]) for layer in data["layers"]))
        self.assertEqual(names, {"door", "player"})
        self.assertEqual(_door_target(self.maps / "generic_levels_4" / "fase_4_2.tmx"), "exp_fase_5")
        self.assertFalse((self.circuits / "generic_levels_4" / "fase_4_2").exists())

    def test_removing_an_extra_level_reconnects_the_chain_and_deletes_its_files(self):
        self.campaign.insert_after("fase_4", "fase_4_2")

        self.campaign.remove("fase_4_2")

        self.assertEqual(self._scenes()[5:7], ["fase_4", "exp_fase_5"])
        self.assertFalse((self.maps / "generic_levels_4" / "fase_4_2.tmx").exists())
        self.assertFalse((self.circuits / "generic_levels_4" / "fase_4_2").exists())

    def test_moving_an_extra_level_changes_its_place_in_the_stage(self):
        self.campaign.insert_after("fase_4", "fase_4_2")
        self.campaign.insert_after("fase_4_2", "fase_4_3")

        self.campaign.move("fase_4_3", after="fase_4")

        self.assertEqual(self._scenes()[5:9], ["fase_4", "fase_4_3", "fase_4_2", "exp_fase_5"])

    def test_original_levels_cannot_be_removed(self):
        with self.assertRaisesRegex(CampaignError, "original"):
            self.campaign.remove("fase_4")

    def test_duplicate_scene_names_are_rejected(self):
        with self.assertRaisesRegex(CampaignError, "exp_fase_5"):
            self.campaign.insert_after("fase_4", "exp_fase_5")

    def test_scene_names_must_be_simple_identifiers(self):
        with self.assertRaises(CampaignError):
            self.campaign.insert_after("fase_4", "../fase")

    def test_nothing_can_follow_the_final_level(self):
        with self.assertRaisesRegex(CampaignError, "fase_8"):
            self.campaign.insert_after("fase_8", "fase_8_2")

    def test_levels_cannot_move_to_another_stage(self):
        self.campaign.insert_after("fase_4", "fase_4_2")

        with self.assertRaises(CampaignError):
            self.campaign.move("fase_4_2", after="fase_7")

    def test_suggested_name_is_the_next_free_one_in_the_stage(self):
        self.campaign.insert_after("fase_4", "fase_4_2")

        self.assertEqual(self.campaign.suggest_name(4), "fase_4_3")

    def test_level_in_a_stage_folder_not_reached_by_any_door_is_reported(self):
        shutil.copy(self.maps / "generic_levels_4" / "fase_4.tmx", self.maps / "generic_levels_4" / "orphan.tmx")

        self.assertIn("orphan", " ".join(self.campaign.issues()))


if __name__ == "__main__":
    unittest.main()
