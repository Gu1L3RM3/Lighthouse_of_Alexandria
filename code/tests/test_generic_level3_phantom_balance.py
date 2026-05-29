import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.components.health import Health
from core.managers.bomb_manager import BombManager
from entities.enemies.enemy_factory import EnemyFactory


class _FakePhantom:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class GenericLevel3PhantomBalanceTest(unittest.TestCase):
    def _load_level3_phantom_properties(self) -> dict[str, str]:
        tmx_path = ROOT.parent / "assets" / "maps" / "fases" / "generic_levels_3" / "fase_3.tmx"
        tree = ET.parse(tmx_path)
        root = tree.getroot()
        for object_group in root.findall("objectgroup"):
            if object_group.attrib.get("name") != "enemies":
                continue
            for obj in object_group.findall("object"):
                name = obj.attrib.get("name", "")
                properties = obj.find("properties")
                if name != "phantom_guard_1" or properties is None:
                    continue
                return {
                    prop.attrib["name"]: prop.attrib.get("value", "")
                    for prop in properties.findall("property")
                }
        self.fail("phantom_guard_1 not found in generic_levels_3/fase_3.tmx")

    def test_level3_phantom_is_tuned_for_easy_bomb_kill(self):
        props = self._load_level3_phantom_properties()

        self.assertEqual("40", props.get("hp"))
        self.assertEqual("48", props.get("chase_speed"))

        original_registry = dict(EnemyFactory._registry)
        try:
            EnemyFactory._registry["phantom"] = _FakePhantom
            phantom = EnemyFactory.create("phantom", 640.0, 496.0, props=props, route=[])
        finally:
            EnemyFactory._registry = original_registry

        self.assertEqual(40.0, phantom.kwargs["max_hp"])
        self.assertEqual(48.0, phantom.kwargs["chase_speed"])

    def test_standard_bomb_damage_kills_level3_phantom(self):
        bomb_manager = BombManager(bombs_per_level=1, default_netlist_path=None)
        phantom_health = Health(max_hp=40.0)

        died = phantom_health.take_damage(bomb_manager.default_params.damage)

        self.assertEqual(40.0, bomb_manager.default_params.damage)
        self.assertTrue(died)
        self.assertEqual(0.0, phantom_health.current_hp)


if __name__ == "__main__":
    unittest.main()
