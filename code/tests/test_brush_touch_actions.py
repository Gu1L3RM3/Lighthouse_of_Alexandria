import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.components.connectable import Connectable
from core.ecs import Entity
from core.ui.widgets.brush_touch_actions import BrushTouchActions

BUTTON_SIZE = (110, 74)


class FakeInputSystem:
    def __init__(self):
        self.brush = None
        self.rotations = 0
        self.exits = 0

    def rotate_brush(self):
        self.rotations += 1

    def exit_current_tool(self):
        self.exits += 1
        self.brush = None


def rotatable_part():
    part = Entity()
    part.add(Connectable({"left", "right"}))
    return part


class BrushTouchActionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.input_system = FakeInputSystem()
        self.source = "touch"
        self.popup_open = False
        self.actions = BrushTouchActions(
            self.input_system,
            pygame.Surface(BUTTON_SIZE),
            pygame.Surface(BUTTON_SIZE),
            bottom_left=(12, 708),
            input_source=lambda: self.source,
            popup_open=lambda: self.popup_open,
        )

    def visible_names(self):
        self.actions.update(1 / 60)
        return self.actions.visible_button_names()

    def test_shows_rotate_and_cancel_while_holding_a_part_by_touch(self):
        self.input_system.brush = rotatable_part()
        self.assertEqual(self.visible_names(), ["rotate", "cancel"])

    def test_hides_rotate_for_tools_that_cannot_turn(self):
        self.input_system.brush = Entity()
        self.assertEqual(self.visible_names(), ["cancel"])

    def test_stays_hidden_with_empty_hands(self):
        self.assertEqual(self.visible_names(), [])

    def test_stays_hidden_for_mouse_players(self):
        self.input_system.brush = rotatable_part()
        self.source = "mouse"
        self.assertEqual(self.visible_names(), [])

    def test_stays_hidden_while_a_popup_is_open(self):
        self.input_system.brush = rotatable_part()
        self.popup_open = True
        self.assertEqual(self.visible_names(), [])

    def test_rotate_turns_the_held_part(self):
        self.input_system.brush = rotatable_part()
        self.actions.update(1 / 60)
        self.actions.buttons["rotate"].activate()
        self.assertEqual(self.input_system.rotations, 1)

    def test_cancel_drops_the_tool(self):
        self.input_system.brush = rotatable_part()
        self.actions.update(1 / 60)
        self.actions.buttons["cancel"].activate()
        self.assertEqual(self.input_system.exits, 1)

    def test_blocks_the_grid_only_where_buttons_are_shown(self):
        self.assertEqual(self.actions.rects(), [])
        self.input_system.brush = rotatable_part()
        self.actions.update(1 / 60)
        rects = self.actions.rects()
        self.assertEqual(len(rects), 2)
        self.assertEqual(rects[0].bottomleft, (12, 708))


if __name__ == "__main__":
    unittest.main()
