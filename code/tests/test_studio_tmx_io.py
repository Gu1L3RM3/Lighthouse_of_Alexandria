import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.append(str(REPO / "tools"))

from studio.tmx_io import TmxDocument, TmxFormatError

MAPS_DIR = REPO / "assets" / "maps" / "fases"
LEVEL3 = MAPS_DIR / "generic_levels_3" / "fase_3.tmx"


class TmxIoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _copy_level3(self) -> Path:
        target = self.tmp / "fase_3.tmx"
        shutil.copy(LEVEL3, target)
        return target

    def test_saving_unchanged_map_writes_the_same_bytes_for_every_level(self):
        for tmx in sorted(MAPS_DIR.rglob("*.tmx")):
            with self.subTest(map=tmx.name):
                target = self.tmp / tmx.name
                document = TmxDocument(tmx)
                document.update(document.to_dict())
                document.save(target)

                self.assertEqual(target.read_bytes(), tmx.read_bytes())

    def test_reads_size_tilesets_layers_and_objects(self):
        data = TmxDocument(LEVEL3).to_dict()

        self.assertEqual((data["width"], data["height"], data["tilewidth"]), (64, 64, 16))
        self.assertEqual(data["tilesets"][0]["firstgid"], 1)
        self.assertTrue(data["tilesets"][0]["image"].endswith("Dungeon_Tileset.png"))
        ground = next(layer for layer in data["layers"] if layer["name"] == "ground")
        self.assertEqual(len(ground["data"]), 64 * 64)
        door = next(group for group in data["objectgroups"] if group["name"] == "door")["objects"][0]
        self.assertEqual(door["properties"], [{"name": "next_scene", "type": "string", "value": "exp_fase_4"}])

    def test_painting_a_tile_is_saved(self):
        path = self._copy_level3()
        document = TmxDocument(path)
        data = document.to_dict()
        obj_layer = next(layer for layer in data["layers"] if layer["name"] == "obj")
        obj_layer["data"][0] = 7

        document.update(data)
        document.save()

        reloaded = next(layer for layer in TmxDocument(path).to_dict()["layers"] if layer["name"] == "obj")
        self.assertEqual(reloaded["data"][0], 7)

    def test_moving_an_object_and_editing_a_property_keeps_its_shape(self):
        path = self._copy_level3()
        document = TmxDocument(path)
        data = document.to_dict()
        panel = next(
            obj for group in data["objectgroups"] for obj in group["objects"] if obj.get("name") == "control_pannel"
        )
        panel["x"] = 100.5
        target = next(prop for prop in panel["properties"] if prop["name"] == "target_component")
        target["value"] = "R2"

        document.update(data)
        document.save()

        reloaded = next(
            obj
            for group in TmxDocument(path).to_dict()["objectgroups"]
            for obj in group["objects"]
            if obj["id"] == panel["id"]
        )
        self.assertEqual(reloaded["x"], 100.5)
        self.assertEqual(reloaded["shape"], "point")
        self.assertIn({"name": "target_component", "type": "string", "value": "R2"}, reloaded["properties"])

    def test_new_objects_get_fresh_ids_and_removed_objects_disappear(self):
        path = self._copy_level3()
        document = TmxDocument(path)
        data = document.to_dict()
        next_id = data["nextobjectid"]
        items = next(group for group in data["objectgroups"] if group["name"] == "itens")
        removed_id = items["objects"].pop(0)["id"]
        items["objects"].append(
            {"name": "resistor", "x": 10, "y": 20, "shape": "point",
             "properties": [{"name": "valor", "type": "string", "value": "220"}]}
        )

        document.update(data)
        document.save()

        reloaded = TmxDocument(path).to_dict()
        ids = [obj["id"] for group in reloaded["objectgroups"] for obj in group["objects"]]
        self.assertNotIn(removed_id, ids)
        self.assertIn(next_id, ids)
        self.assertEqual(reloaded["nextobjectid"], next_id + 1)

    def test_non_csv_layers_are_rejected(self):
        path = self._copy_level3()
        path.write_text(path.read_text(encoding="utf-8").replace('encoding="csv"', 'encoding="base64"', 1), encoding="utf-8")

        with self.assertRaises(TmxFormatError):
            TmxDocument(path).to_dict()


if __name__ == "__main__":
    unittest.main()
