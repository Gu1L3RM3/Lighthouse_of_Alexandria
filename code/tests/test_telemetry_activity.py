import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from core.telemetry.activity import has_player_input


class PlayerInputTest(unittest.TestCase):
    def test_key_press_counts_as_input(self):
        self.assertTrue(has_player_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)]))

    def test_finger_down_counts_as_input(self):
        self.assertTrue(has_player_input([pygame.event.Event(pygame.FINGERDOWN, x=0.1, y=0.1, finger_id=1)]))

    def test_window_events_do_not_count_as_input(self):
        self.assertFalse(has_player_input([pygame.event.Event(pygame.VIDEOEXPOSE)]))


if __name__ == "__main__":
    unittest.main()
