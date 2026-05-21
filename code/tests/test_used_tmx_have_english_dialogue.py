import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


USED_TMX_FILES = [
    ROOT.parent / "assets" / "maps" / "house.tmx",
    ROOT.parent / "assets" / "maps" / "house_after.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "fase_1.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "fase_2.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "exp_fase_3.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "exp_fase_4.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "exp_fase_5.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "exp_fase_6.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "exp_fase_7.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_3" / "fase_3.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_4" / "fase_4.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_5" / "fase_5.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_6" / "fase_6.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_7" / "fase_7.tmx",
    ROOT.parent / "assets" / "maps" / "fases" / "final_fase" / "fase_8.tmx",
]


class UsedTmxEnglishDialogueAuditTest(unittest.TestCase):
    def test_every_used_tmx_dialogue_has_english_variant(self):
        missing = []

        for tmx_path in USED_TMX_FILES:
            tree = ET.parse(tmx_path)
            root = tree.getroot()
            for obj in root.findall(".//object"):
                properties = obj.find("properties")
                if properties is None:
                    continue

                dialogo = None
                dialogo_en = None
                for prop in properties.findall("property"):
                    name = prop.get("name")
                    value = prop.get("value") or (prop.text or "")
                    if name == "dialogo":
                        dialogo = value.strip()
                    elif name == "dialogo_en":
                        dialogo_en = value.strip()

                if dialogo and not dialogo_en:
                    missing.append(f"{tmx_path.name}:{obj.get('name', '<unnamed>')}")

        self.assertEqual(
            missing,
            [],
            "TMX usados pelo jogo ainda sem dialogo_en: " + ", ".join(missing),
        )


if __name__ == "__main__":
    unittest.main()
