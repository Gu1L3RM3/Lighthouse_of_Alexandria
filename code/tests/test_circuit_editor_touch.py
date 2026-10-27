import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.components.connectable import Connectable
from core.components.dropped import Dropped
from core.components.position import Position
from core.components.sprite import Sprite
from core.ecs import Entity
from core.systems.circuit_editor.input_system import InputSystem
from core.ui.touch_grid import aim_position, grid_lift_positions

CELL = 32
FAR_CELL = pygame.Rect(320, 320, CELL, CELL)


def make_system_with_brush():
    system = InputSystem.__new__(InputSystem)
    system.grid_rects = [pygame.Rect(0, 0, CELL, CELL), FAR_CELL]
    brush = Entity()
    brush.add(Position(0, 0))
    brush.add(Sprite(pygame.Surface((CELL, CELL)), offset_x=2, offset_y=3))
    system.brush = brush
    system.pointer_position = lambda: FAR_CELL.center
    return system, brush


class CircuitEditorTouchTest(unittest.TestCase):
    def test_aiming_the_brush_moves_its_hitbox_too(self):
        system, brush = make_system_with_brush()
        system.update_brush_position()
        self.assertEqual(brush.get(Sprite).rect.topleft, (FAR_CELL.x + 2, FAR_CELL.y + 3))

    def test_brush_follows_the_pointer_not_the_mouse(self):
        system, brush = make_system_with_brush()
        with mock.patch("pygame.mouse.get_pos", return_value=(1, 1)):
            system.update_brush_position()
        self.assertEqual(brush.get(Position).xy_tuple(), FAR_CELL.topleft)

    def test_rotating_the_held_part_turns_it(self):
        # used to crash the game: input_system never imported Connectable
        system, brush = make_system_with_brush()
        system.angle_deg = 90
        brush.add(Connectable({"left", "right"}))
        system.rotate_brush()
        self.assertEqual(brush.get(Sprite).angle, 90)

    def test_grid_action_aims_the_brush_at_the_tap_before_acting(self):
        # a finger has no hover, so the brush is still at the previous cell when the tap lands
        system, brush = make_system_with_brush()
        aimed_at = []
        system.drop_entity = lambda: aimed_at.append(brush.get(Sprite).rect.topleft)
        for name in ("delete_entity", "rotate_entity", "select_entity", "change_drop_status"):
            setattr(system, name, lambda: None)
        system.handle_canvas_actions()
        self.assertEqual(aimed_at, [(FAR_CELL.x + 2, FAR_CELL.y + 3)])



class _Entities:
    def __init__(self, *entities):
        self.entities = list(entities)

    def get_entities(self):
        return list(self.entities)


def placed_part_at(rect):
    part = Entity()
    sprite = Sprite(pygame.Surface(rect.size))
    sprite.rect.topleft = rect.topleft
    part.add(sprite)
    return part


class CanDropBrushTest(unittest.TestCase):
    def setUp(self):
        self.system, self.brush = make_system_with_brush()
        self.brush.add(Dropped())
        self.system.update_brush_position()

    def test_brush_can_drop_on_a_free_cell(self):
        self.system.entity_manager = _Entities(self.brush, placed_part_at(pygame.Rect(0, 0, CELL, CELL)))
        self.assertTrue(self.system.can_drop_brush())

    def test_brush_cannot_drop_where_a_part_already_is(self):
        self.system.entity_manager = _Entities(self.brush, placed_part_at(FAR_CELL))
        self.assertFalse(self.system.can_drop_brush())

    def test_tool_brush_is_not_droppable(self):
        self.brush.remove(Dropped)
        self.system.entity_manager = _Entities(self.brush)
        self.assertFalse(self.system.can_drop_brush())



class GridLiftPositionsTest(unittest.TestCase):
    GRID = pygame.Rect(0, 128, 1280, 592)
    SIDEBAR = pygame.Rect(1142, 0, 138, 720)

    def test_lift_on_the_grid_counts(self):
        self.assertEqual(grid_lift_positions([(300, 300)], self.GRID, [self.SIDEBAR]), [(300, 300)])

    def test_lift_on_a_menu_over_the_grid_is_ignored(self):
        self.assertEqual(grid_lift_positions([(1200, 300)], self.GRID, [self.SIDEBAR]), [])

    def test_lift_outside_the_grid_is_ignored(self):
        self.assertEqual(grid_lift_positions([(300, 40)], self.GRID, []), [])



class AimPositionTest(unittest.TestCase):
    BUTTON = pygame.Rect(12, 634, 110, 74)

    def test_finger_on_the_grid_becomes_the_aim(self):
        self.assertEqual(aim_position((300, 300), [self.BUTTON], previous=(10, 10)), (300, 300))

    def test_tapping_a_button_over_the_grid_keeps_the_previous_aim(self):
        self.assertEqual(aim_position(self.BUTTON.center, [self.BUTTON], previous=(300, 300)), (300, 300))

    def test_without_any_touch_the_aim_stays(self):
        self.assertEqual(aim_position(None, [], previous=(300, 300)), (300, 300))


if __name__ == "__main__":
    unittest.main()
