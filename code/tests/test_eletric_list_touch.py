import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.touch_points import TouchPoints
from core.ui.widgets.eletric_list import EletricList

SCREEN_SIZE = (1280, 720)
VALUES = {f"{ohms}": 1 for ohms in range(100, 2100, 100)}


class Storage:
    revision = 0
    storage_circuit = {"Resistor": VALUES}


class FakeClock:
    def __call__(self):
        return 0


def finger(event_type, pos):
    return pygame.event.Event(event_type, finger_id=1, x=pos[0] / SCREEN_SIZE[0], y=pos[1] / SCREEN_SIZE[1])


class EletricListTouchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode(SCREEN_SIZE)

    def setUp(self):
        # the list's item buttons read the shared tracker, so the test installs a fresh one
        self.touches = TouchPoints(SCREEN_SIZE, clock=FakeClock())
        self._previous_touches = TouchPoints._instance
        TouchPoints._instance = self.touches
        self.addCleanup(setattr, TouchPoints, "_instance", self._previous_touches)
        self.picked = []
        self.list = EletricList(
            Storage.storage_circuit,
            "Resistor",
            storage_manager=Storage(),
            action=lambda list_type, value: self.picked.append(value),
            touch_points=self.touches,
        )

    def frame(self, *events):
        self.touches.begin_frame()
        for event in events:
            self.touches.handle_event(event)
        self.list.update(1 / 60)

    def test_dragging_up_scrolls_the_list_without_picking(self):
        start = self.list.content_view_rect.center
        self.frame(finger(pygame.FINGERDOWN, start))
        for step in range(1, 7):
            self.frame(finger(pygame.FINGERMOTION, (start[0], start[1] - step * 20)))
        end = (start[0], start[1] - 120)
        self.frame(finger(pygame.FINGERUP, end))
        self.frame()
        self.assertEqual(self.list.scroll_offset, 120)
        self.assertEqual(self.picked, [])

    def test_tapping_an_item_picks_it(self):
        first = self.list.visible_buttons[0]._rect.center
        self.frame(finger(pygame.FINGERDOWN, first), finger(pygame.FINGERUP, first))
        self.frame()
        self.assertEqual(self.picked, ["100"])

    def test_small_jitter_still_counts_as_a_tap(self):
        first = self.list.visible_buttons[0]._rect.center
        self.frame(finger(pygame.FINGERDOWN, first))
        self.frame(finger(pygame.FINGERMOTION, (first[0], first[1] - 3)))
        self.frame(finger(pygame.FINGERUP, (first[0], first[1] - 3)))
        self.assertEqual(self.picked, ["100"])


if __name__ == "__main__":
    unittest.main()
