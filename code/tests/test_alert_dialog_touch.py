import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.touch_points import TouchPoints
from core.ui.widgets.alert_dialog import AlertDialog

SCREEN_SIZE = (1280, 720)
OUTSIDE = (100, 100)


class FakeClock:
    def __call__(self):
        return 0


def finger_down(pos):
    return pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=pos[0] / SCREEN_SIZE[0], y=pos[1] / SCREEN_SIZE[1])


class AlertDialogTouchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode(SCREEN_SIZE)

    def setUp(self):
        self.touches = TouchPoints(SCREEN_SIZE, clock=FakeClock())
        self.closed = []
        self.dialog = AlertDialog(
            title="List",
            on_close=self.closed.append,
            dialog_size=(300, 200),
            make_freeze=False,
            touch_points=self.touches,
        )

    def frame(self, *events):
        self.touches.begin_frame()
        for event in events:
            self.touches.handle_event(event)
        self.dialog.update(1 / 60)

    def test_touch_outside_closes_the_dialog(self):
        self.frame()
        self.frame(finger_down(OUTSIDE))
        self.assertEqual(self.closed, [self.dialog])

    def test_touch_inside_keeps_the_dialog_open(self):
        self.frame()
        self.frame(finger_down(self.dialog.dialog_rect.center))
        self.assertEqual(self.closed, [])

    def test_the_touch_that_opened_the_dialog_does_not_close_it(self):
        # the dialog is built while handling that very touch, so it sees it in its first update
        self.touches.handle_event(finger_down(OUTSIDE))
        self.dialog.update(1 / 60)
        self.assertEqual(self.closed, [])

    def test_reopened_dialog_ignores_the_touch_that_reopened_it(self):
        # the component lists reuse one dialog: hidden for a while, then shown by a tap outside it
        self.frame()
        self.touches.begin_frame()
        self.touches.begin_frame()
        self.frame(finger_down(OUTSIDE))
        self.assertEqual(self.closed, [])


if __name__ == "__main__":
    unittest.main()
