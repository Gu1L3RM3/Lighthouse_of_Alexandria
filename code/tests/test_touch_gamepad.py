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

SCREEN_SIZE = (1280, 720)


def finger_event(event_type, pad, control, finger_id=1, offset=(0, 0)):
    center = pad.controls[control].center
    return pygame.event.Event(
        event_type,
        finger_id=finger_id,
        x=(center[0] + offset[0]) / SCREEN_SIZE[0],
        y=(center[1] + offset[1]) / SCREEN_SIZE[1],
    )


class TouchGamepadTest(unittest.TestCase):
    def setUp(self):
        self.pad = TouchGamepad(SCREEN_SIZE)

    def test_is_hidden_until_the_screen_is_touched(self):
        self.assertFalse(self.pad.active)
        self.pad.handle_event(pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5))
        self.assertTrue(self.pad.active)

    def test_finger_on_left_of_dpad_points_left(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(-80, 0)))
        self.assertEqual(self.pad.direction, (-1, 0))

    def test_finger_on_dpad_diagonal_points_diagonally(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(70, 70)))
        self.assertEqual(self.pad.direction, (1, 1))

    def test_finger_on_dpad_center_points_nowhere(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "dpad"))
        self.assertEqual(self.pad.direction, (0, 0))

    def test_sliding_finger_on_dpad_changes_direction(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(-80, 0)))
        self.pad.handle_event(finger_event(pygame.FINGERMOTION, self.pad, "dpad", offset=(0, -80)))
        self.assertEqual(self.pad.direction, (0, -1))

    def test_finger_on_a_button_presses_confirm_and_interact(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "a"))
        self.assertEqual(self.pad.pressed_actions, {"confirm", "interact"})

    def test_lifting_finger_releases_its_button_only(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "a", finger_id=1))
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "x", finger_id=2))
        self.pad.handle_event(finger_event(pygame.FINGERUP, self.pad, "a", finger_id=1))
        self.assertEqual(self.pad.pressed_actions, {"bomb"})

    def test_mouse_click_over_a_control_is_consumed_once_active(self):
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=self.pad.controls["b"].center, button=1)
        self.assertFalse(self.pad.handle_event(click))
        self.pad.handle_event(pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5))
        self.assertTrue(self.pad.handle_event(click))

    def test_mouse_click_away_from_controls_reaches_the_game(self):
        self.pad.handle_event(pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5))
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 360), button=1)
        self.assertFalse(self.pad.handle_event(click))

    def test_physical_key_press_hides_the_pad_and_releases_everything(self):
        self.pad.handle_event(finger_event(pygame.FINGERDOWN, self.pad, "a"))
        self.pad.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
        self.assertFalse(self.pad.active)
        self.assertEqual(self.pad.pressed_actions, set())

    def test_controls_scale_with_the_screen(self):
        small = TouchGamepad((640, 360))
        self.assertEqual(small.controls["a"].center, (self.pad.controls["a"].centerx // 2, self.pad.controls["a"].centery // 2))


class InputManagerTouchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.input_manager = InputManager()
        self.pad = TouchGamepad(SCREEN_SIZE)
        self.input_manager.touch_gamepad = self.pad
        self.input_manager.touch_points = TouchPoints(SCREEN_SIZE)

    def test_touching_a_button_triggers_its_action(self):
        events = self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "a")])
        self.assertTrue(self.input_manager.is_action_just_pressed("confirm"))
        self.assertIn(pygame.K_RETURN, [e.key for e in events if e.type == pygame.KEYDOWN])

    def test_touch_switches_prompts_to_controller_labels(self):
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "b")])
        self.assertEqual(self.input_manager.get_prompt_button("back"), "B")

    def test_controller_button_labels_ignore_the_last_input_source(self):
        self.input_manager.last_input_source = "mouse"
        self.assertEqual(self.input_manager.get_controller_button("confirm"), "A")
        self.assertEqual(self.input_manager.get_controller_button("pause"), "START")

    def test_holding_the_dpad_keeps_moving_on_frames_without_events(self):
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(80, 0))])
        self.input_manager.process_events([])
        self.assertEqual(tuple(self.input_manager.get_movement_vector()), (1.0, 0.0))

    def test_releasing_the_dpad_stops_movement(self):
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(80, 0))])
        self.input_manager.process_events([finger_event(pygame.FINGERUP, self.pad, "dpad", offset=(80, 0))])
        self.assertEqual(tuple(self.input_manager.get_movement_vector()), (0.0, 0.0))

    def test_active_touch_pad_counts_as_a_controller(self):
        self.assertFalse(self.input_manager.has_controller())
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "dpad")])
        self.assertTrue(self.input_manager.has_controller())

    def test_mouse_click_over_a_control_does_not_reach_the_game(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=9, x=0.5, y=0.5)])
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=self.pad.controls["a"].center, button=1)
        self.assertNotIn(click, self.input_manager.process_events([click]))

    def test_finger_away_from_the_pad_switches_input_to_touch(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5)])
        self.assertEqual(self.input_manager.last_input_source, "touch")

    def test_emulated_mouse_click_after_a_touch_keeps_touch_input(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5)])
        click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 360), button=1)
        self.input_manager.process_events([click])
        self.assertEqual(self.input_manager.last_input_source, "touch")

    def test_pointer_follows_the_finger_on_touch(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.25)])
        with mock.patch("pygame.mouse.get_pos", return_value=(1, 1)):
            self.assertEqual(self.input_manager.get_pointer_position(), (640, 180))

    def test_pointer_is_the_mouse_without_touch(self):
        with mock.patch("pygame.mouse.get_pos", return_value=(12, 34)):
            self.assertEqual(self.input_manager.get_pointer_position(), (12, 34))

    def test_disabled_pad_leaves_touches_on_its_area_to_the_scene(self):
        self.input_manager.set_touch_gamepad_enabled(False)
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "a")])
        self.assertFalse(self.input_manager.is_action_just_pressed("confirm"))
        self.assertEqual(self.input_manager.touch_points.pressed_positions(), [self.pad.controls["a"].center])

    def test_disabled_pad_does_not_count_as_a_controller(self):
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "dpad")])
        self.input_manager.set_touch_gamepad_enabled(False)
        self.assertFalse(self.input_manager.has_controller())

    def test_disabling_the_pad_releases_what_it_held(self):
        self.input_manager.process_events([finger_event(pygame.FINGERDOWN, self.pad, "dpad", offset=(80, 0))])
        self.input_manager.set_touch_gamepad_enabled(False)
        events = self.input_manager.process_events([])
        self.assertEqual(tuple(self.input_manager.get_movement_vector()), (0.0, 0.0))
        self.assertIn(pygame.K_RIGHT, [e.key for e in events if e.type == pygame.KEYUP])

    def test_touch_players_see_the_on_screen_pad_names_in_prompts(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5)])
        self.assertEqual([chip for chip, _ in self.input_manager.get_prompt_items("menu")], ["D-PAD", "A", "B"])
        self.assertEqual(self.input_manager.get_prompt_button("pause"), "START")

    def test_touch_prompt_area_sits_between_the_pad_controls(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5)])
        area = self.input_manager.touch_prompt_area()
        self.assertGreater(area.left, self.pad.controls["dpad"].right)
        self.assertLess(area.right, self.pad.controls["x"].left)
        self.assertLessEqual(area.bottom, SCREEN_SIZE[1])

    def test_no_touch_prompt_area_before_the_pad_shows_up(self):
        self.assertIsNone(self.input_manager.touch_prompt_area())

    def test_no_touch_prompt_area_where_the_pad_is_switched_off(self):
        self.input_manager.process_events([pygame.event.Event(pygame.FINGERDOWN, finger_id=1, x=0.5, y=0.5)])
        self.input_manager.set_touch_gamepad_enabled(False)
        self.assertIsNone(self.input_manager.touch_prompt_area())


if __name__ == "__main__":
    unittest.main()
