import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.components.sprite import Sprite

WEB_SCREEN = (1280, 720)
# Has parts at x = 1152, the columns the sidebar used to cover on the web build.
WIDE_CIRCUIT = "generic_levels_4/fase_4/pannel3"


class CircuitEditorBoardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode(WEB_SCREEN)
        from scenes.circuit_editor import CircuitEditor
        cls.editor = CircuitEditor(cls.screen, WIDE_CIRCUIT)
        cls.editor.update(1 / 60)
        cls.editor.render()

    def test_every_part_of_a_wide_circuit_is_on_the_visible_board(self):
        board = self.editor.board
        for entity in self.editor.entity_mn.get_entities_with(Sprite):
            with self.subTest(part=type(entity).__name__):
                self.assertTrue(board.screen_rect.contains(board.to_screen_rect(entity.get(Sprite).rect)))

    def test_clicks_on_the_sidebar_never_reach_the_grid(self):
        self.assertLessEqual(self.editor.gesture_canvas.rect.right, self.editor.menu_widget.rect_right.left)

    def test_clicks_on_the_top_bar_never_reach_the_grid(self):
        self.assertGreaterEqual(self.editor.gesture_canvas.rect.top, self.editor.menu_widget.rect_top.bottom)


if __name__ == "__main__":
    unittest.main()
