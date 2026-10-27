import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.managers.input_manager import InputManager
from core.touch_gamepad import TouchGamepad
from core.touch_points import TouchPoints
from core.ui.widgets.gesture_detector import ClickType, GestureDetector

SCREEN_SIZE = (1280, 720)
BUTTON_RECT = pygame.Rect(600, 300, 200, 80)


class FakeClock:
    def __init__(self):
        self.ms = 10_000

    def __call__(self):
        return self.ms


def finger(event_type, pos, finger_id=1):
    return pygame.event.Event(event_type, finger_id=finger_id, x=pos[0] / SCREEN_SIZE[0], y=pos[1] / SCREEN_SIZE[1])


class TouchButtonTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.touches = TouchPoints(SCREEN_SIZE, clock=self.clock)
        self.calls = 0
        self.detector = GestureDetector(BUTTON_RECT.size, self._count, ClickType.AFTER_RELEASED, touch_points=self.touches)
        self.detector.rect.topleft = BUTTON_RECT.topleft

    def _count(self):
        self.calls += 1

    def frame(self, *events):
        self.touches.begin_frame()
        for event in events:
            self.touches.handle_event(event)
        self.detector.update(1 / 60)

    def test_tap_within_one_frame_triggers_the_button_once(self):
        self.frame(finger(pygame.FINGERDOWN, BUTTON_RECT.center), finger(pygame.FINGERUP, BUTTON_RECT.center))
        self.frame()
        self.frame()
        self.assertEqual(self.calls, 1)

    def test_held_touch_triggers_only_when_lifted(self):
        self.frame(finger(pygame.FINGERDOWN, BUTTON_RECT.center))
        self.frame()
        self.assertEqual(self.calls, 0)
        self.frame(finger(pygame.FINGERUP, BUTTON_RECT.center))
        self.assertEqual(self.calls, 1)

    def test_touch_shows_the_button_pressed_while_held(self):
        self.frame(finger(pygame.FINGERDOWN, BUTTON_RECT.center))
        self.assertTrue(self.detector.is_pressed)

    def test_sliding_off_the_button_before_lifting_cancels_it(self):
        self.frame(finger(pygame.FINGERDOWN, BUTTON_RECT.center))
        self.frame(finger(pygame.FINGERMOTION, (50, 50)))
        self.frame(finger(pygame.FINGERUP, (50, 50)))
        self.assertEqual(self.calls, 0)

    def test_touch_outside_the_button_does_nothing(self):
        self.frame(finger(pygame.FINGERDOWN, (50, 50)), finger(pygame.FINGERUP, (50, 50)))
        self.frame()
        self.assertEqual(self.calls, 0)

    def test_after_press_button_fires_on_touch_down(self):
        detector = GestureDetector(BUTTON_RECT.size, self._count, ClickType.AFTER_PRESSED, touch_points=self.touches)
        detector.rect.topleft = BUTTON_RECT.topleft
        self.touches.begin_frame()
        self.touches.handle_event(finger(pygame.FINGERDOWN, BUTTON_RECT.center))
        detector.update(1 / 60)
        self.assertEqual(self.calls, 1)

    def test_emulated_mouse_click_right_after_a_touch_is_ignored(self):
        self.frame(finger(pygame.FINGERDOWN, (50, 50)), finger(pygame.FINGERUP, (50, 50)))
        self.frame()
        with mock.patch("pygame.mouse.get_pos", return_value=BUTTON_RECT.center), \
                mock.patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            self.frame()
        self.frame()
        self.assertEqual(self.calls, 0)

    def test_real_mouse_click_works_once_touches_have_settled(self):
        self.frame(finger(pygame.FINGERDOWN, (50, 50)), finger(pygame.FINGERUP, (50, 50)))
        self.frame()
        self.clock.ms += 2_000
        with mock.patch("pygame.mouse.get_pos", return_value=BUTTON_RECT.center):
            with mock.patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
                self.frame()
            self.frame()
        self.assertEqual(self.calls, 1)


class TouchPointsTest(unittest.TestCase):
    def test_last_position_is_kept_after_the_finger_lifts(self):
        touches = TouchPoints(SCREEN_SIZE, clock=FakeClock())
        touches.handle_event(finger(pygame.FINGERDOWN, (100, 200)))
        touches.handle_event(finger(pygame.FINGERMOTION, (300, 400)))
        touches.handle_event(finger(pygame.FINGERUP, (300, 400)))
        touches.begin_frame()
        touches.begin_frame()
        self.assertEqual(touches.last_position(), (300, 400))

    def test_last_position_is_none_before_any_touch(self):
        self.assertIsNone(TouchPoints(SCREEN_SIZE, clock=FakeClock()).last_position())


class GestureDetectorTouchOptOutTest(unittest.TestCase):
    def test_detector_that_refuses_touch_ignores_fingers(self):
        touches = TouchPoints(SCREEN_SIZE, clock=FakeClock())
        calls = []
        detector = GestureDetector(BUTTON_RECT.size, lambda: calls.append(1), ClickType.AFTER_PRESSED,
                                   touch_points=touches, accepts_touch=False)
        detector.rect.topleft = BUTTON_RECT.topleft
        touches.handle_event(finger(pygame.FINGERDOWN, BUTTON_RECT.center))
        with mock.patch("pygame.mouse.get_pressed", return_value=(False, False, False)):
            detector.update(1 / 60)
        self.assertEqual(calls, [])


class InputManagerTouchPointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.input_manager = InputManager()
        self.touches = TouchPoints(SCREEN_SIZE, clock=FakeClock())
        self.pad = TouchGamepad(SCREEN_SIZE)
        self.input_manager.touch_points = self.touches
        self.input_manager.touch_gamepad = self.pad

    def test_touches_reach_the_buttons(self):
        self.input_manager.process_events([finger(pygame.FINGERDOWN, BUTTON_RECT.center)])
        self.assertEqual(self.touches.pressed_positions(), [BUTTON_RECT.center])

    def test_fingers_on_the_touch_gamepad_do_not_press_buttons(self):
        self.input_manager.process_events([finger(pygame.FINGERDOWN, self.pad.controls["a"].center)])
        self.assertEqual(self.touches.pressed_positions(), [])


if __name__ == "__main__":
    unittest.main()
