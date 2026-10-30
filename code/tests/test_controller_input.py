import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.managers.input_manager import InputManager
from core.touch_points import TouchPoints


class ControllerInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.manager = InputManager()
        self.manager.touch_points = TouchPoints((1280, 720))
        self.controller = mock.Mock(name="DualSense")
        self.controller.id = 42
        self.controller.name = "Sony DualSense Wireless Controller"
        self.buttons = set()
        self.controller.get_button.side_effect = lambda button: button in self.buttons
        self.controller.get_axis.return_value = 0
        self.manager.controllers = {42: self.controller}
        self.manager._prev_button_states = dict.fromkeys(range(15), False)
        self.manager._xinput = None
        refresh = mock.patch.object(self.manager, "_refresh_connected_joysticks")
        refresh.start()
        self.addCleanup(refresh.stop)

    def button_event(self, event_type, button, instance_id=42):
        return pygame.event.Event(event_type, instance_id=instance_id, button=button)

    def test_quick_playstation_taps_reach_all_game_actions(self):
        for button, actions in {
            0: {"confirm", "interact"},
            1: {"back"},
            2: {"bomb"},
            3: {"open_editor"},
            4: {"help"},
            6: {"pause"},
            7: {"menu_confirm"},
            9: {"tool_prev"},
            10: {"tool_next"},
        }.items():
            with self.subTest(button=button):
                events = self.manager.process_events([
                    self.button_event(pygame.CONTROLLERBUTTONDOWN, button),
                    self.button_event(pygame.CONTROLLERBUTTONUP, button),
                ])
                self.assertEqual(self.manager.just_pressed_actions, actions)
                expected_keys = {
                    key for action in actions for key in self.manager._action_to_keys.get(action, ())
                }
                for event_type in (pygame.KEYDOWN, pygame.KEYUP):
                    self.assertEqual({e.key for e in events if e.type == event_type}, expected_keys)
                self.assertFalse(self.manager._pressed_actions)
                self.assertFalse(self.manager._pressed_virtual_keys)

    def test_event_and_polling_do_not_repeat_held_button(self):
        self.buttons.add(0)
        events = self.manager.process_events([
            self.button_event(pygame.CONTROLLERBUTTONDOWN, 0),
            self.button_event(pygame.JOYBUTTONDOWN, 1),  # Raw PS button numbering differs.
        ])
        self.assertEqual(self.manager.just_pressed_actions, {"confirm", "interact"})
        self.assertEqual(sum(e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN for e in events), 1)
        self.assertFalse(self.manager.process_events([]))
        self.assertFalse(self.manager.just_pressed_actions)
        self.buttons.clear()
        events = self.manager.process_events([self.button_event(pygame.CONTROLLERBUTTONUP, 0)])
        self.assertEqual(sum(e.type == pygame.KEYUP and e.key == pygame.K_RETURN for e in events), 1)
        self.assertFalse(self.manager._pressed_actions)

    def test_polling_still_handles_missing_button_events(self):
        self.buttons.add(2)
        self.manager.process_events([])
        self.assertEqual(self.manager.just_pressed_actions, {"bomb"})
        self.buttons.clear()
        self.manager.process_events([])
        self.assertFalse(self.manager._pressed_actions)

    def test_events_from_other_controllers_are_ignored(self):
        self.manager.process_events([self.button_event(pygame.CONTROLLERBUTTONDOWN, 0, instance_id=99)])
        self.assertFalse(self.manager.just_pressed_actions)

    def test_xinput_does_not_receive_duplicate_sdl_actions(self):
        with mock.patch.object(self.manager, "_poll_xinput_state"):
            self.manager._xinput_connected = True
            self.manager.process_events([self.button_event(pygame.CONTROLLERBUTTONDOWN, 0)])
        self.assertFalse(self.manager.just_pressed_actions)


class WebControllerInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        web = mock.patch("core.managers.input_manager.IS_WEB", True, create=True)
        web.start()
        self.addCleanup(web.stop)
        self.manager = InputManager()
        self.manager.touch_points = TouchPoints((1280, 720))
        self.manager._xinput = None
        self.buttons = set()
        joystick = mock.Mock()
        joystick.get_name.return_value = "Sony DualSense Wireless Controller"
        joystick.get_numbuttons.return_value = 17
        joystick.get_numaxes.return_value = 4
        joystick.get_axis.return_value = 0.0
        joystick.get_numhats.return_value = 0
        joystick.get_button.side_effect = lambda button: button in self.buttons
        self.manager.joysticks = {42: joystick}
        refresh = mock.patch.object(self.manager, "_refresh_connected_joysticks")
        refresh.start()
        self.addCleanup(refresh.stop)

    def test_web_standard_buttons_trigger_the_expected_actions(self):
        for button, actions in {
            0: {"confirm", "interact"}, 1: {"back"}, 2: {"bomb"},
            3: {"open_editor"}, 4: {"tool_prev"}, 5: {"tool_next"},
            6: set(), 7: set(), 8: {"help"}, 9: {"pause"}, 10: {"menu_confirm"},
        }.items():
            with self.subTest(button=button):
                self.buttons.add(button)
                self.manager.process_events([
                    pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=42, button=button)
                ])
                self.assertEqual(self.manager.just_pressed_actions, actions)
                self.manager.process_events([])
                self.assertFalse(self.manager.just_pressed_actions)
                self.buttons.clear()
                self.manager.process_events([
                    pygame.event.Event(pygame.JOYBUTTONUP, instance_id=42, button=button)
                ])
                self.assertFalse(self.manager._pressed_actions)
                self.assertFalse(self.manager._pressed_virtual_keys)

    def test_web_dpad_buttons_move_and_release_in_all_directions(self):
        for buttons, direction, keys in [
            ({12}, (0, -1), {pygame.K_UP}),
            ({13}, (0, 1), {pygame.K_DOWN}),
            ({14}, (-1, 0), {pygame.K_LEFT}),
            ({15}, (1, 0), {pygame.K_RIGHT}),
            ({12, 15}, (1, -1), {pygame.K_UP, pygame.K_RIGHT}),
        ]:
            with self.subTest(buttons=buttons):
                self.buttons.update(buttons)
                events = self.manager.process_events([])
                self.assertEqual(tuple(self.manager.dpad_vector), direction)
                self.assertEqual({e.key for e in events if e.type == pygame.KEYDOWN}, keys)
                self.buttons.clear()
                events = self.manager.process_events([])
                self.assertEqual(tuple(self.manager.dpad_vector), (0, 0))
                self.assertEqual({e.key for e in events if e.type == pygame.KEYUP}, keys)
                self.assertFalse(self.manager._pressed_virtual_keys)


if __name__ == "__main__":
    unittest.main()
