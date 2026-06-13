import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.display_config import DisplayConfigResolver
from core.managers.input_manager import InputManager


class DisplayConfigResolverWebOnlyTest(unittest.TestCase):
    def test_web_runtime_uses_windowed_canvas_size(self):
        config = DisplayConfigResolver.resolve()
        self.assertEqual(config.width, 1280)
        self.assertEqual(config.height, 720)
        self.assertEqual(config.flags, 0)


class InputManagerWebOnlyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        pygame.display.set_mode((32, 32))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_initialize_skips_controller_bootstrap(self):
        manager = InputManager()

        with (
            patch("core.managers.input_manager.pygame.joystick.init") as joystick_init,
            patch("core.managers.input_manager.pygame.joystick.get_count") as get_count,
            patch.object(manager, "apply_mouse_visibility") as apply_mouse_visibility,
        ):
            manager.initialize()

        joystick_init.assert_not_called()
        get_count.assert_not_called()
        apply_mouse_visibility.assert_called_once()
        self.assertFalse(manager.has_controller())

