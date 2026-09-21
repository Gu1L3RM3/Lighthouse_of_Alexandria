import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pygame

from core.ui.widgets.eletric_list import EletricList


class ElectricListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_component_lists_use_canonical_inventory_keys(self):
        components = (
            ("Resistor", "Resistor"),
            ("VoltageSource", "Fonte V"),
            ("CurrentSource", "Fonte I"),
        )
        for component_type, display_name in components:
            with self.subTest(component_type=component_type):
                storage = SimpleNamespace(
                    revision=0,
                    storage_circuit={component_type: {"1": 1}},
                )
                selected = []
                electric_list = EletricList(
                    storage.storage_circuit,
                    component_type,
                    storage_manager=storage,
                    display_name=display_name,
                    action=lambda kind, value: selected.append((kind, value)),
                )

                self.assertEqual(len(electric_list.buttons), 1)
                self.assertIn(display_name, electric_list.buttons[0].text)
                electric_list.buttons[0].action()
                self.assertEqual(selected, [(component_type, "1")])


if __name__ == "__main__":
    unittest.main()
