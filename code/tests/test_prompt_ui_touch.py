import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.ui.prompt_ui import draw_prompt_hint_row

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "PressStart2P-Regular.ttf")
SCREEN_SIZE = (1280, 720)
TOUCH_AREA = pygame.Rect(302, 430, 686, 278)
SHORT_ROW = [("A", "confirm"), ("B", "back")]
LONG_ROW = [("X", "bomb"), ("Y", "editor"), ("BACK", "help"), ("START", "menu"), ("A", "interact")]


def drawn_bounds(items, **kwargs):
    surface = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    font = pygame.font.Font(FONT_PATH, 8)
    draw_prompt_hint_row(surface, font, font, items, anchor=(18, SCREEN_SIZE[1] - 24), align="left", **kwargs)
    return surface.get_bounding_rect()


class PromptHintTouchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_without_touch_the_row_keeps_its_anchor_and_size(self):
        bounds = drawn_bounds(SHORT_ROW, touch_area=None)
        self.assertEqual(bounds.left, 18)
        self.assertLess(bounds.height, 30)

    def test_touch_row_is_twice_as_big_and_centred_in_the_free_area(self):
        normal = drawn_bounds(SHORT_ROW, touch_area=None)
        bounds = drawn_bounds(SHORT_ROW, touch_area=TOUCH_AREA)
        self.assertEqual(bounds.height, normal.height * 2)
        self.assertTrue(TOUCH_AREA.contains(bounds))
        self.assertLessEqual(abs(bounds.centerx - TOUCH_AREA.centerx), 1)

    def test_touch_row_too_wide_for_the_area_wraps_into_two_rows(self):
        one_row = drawn_bounds(SHORT_ROW, touch_area=TOUCH_AREA)
        bounds = drawn_bounds(LONG_ROW, touch_area=TOUCH_AREA)
        self.assertTrue(TOUCH_AREA.contains(bounds))
        self.assertGreater(bounds.height, one_row.height * 2)


if __name__ == "__main__":
    unittest.main()
