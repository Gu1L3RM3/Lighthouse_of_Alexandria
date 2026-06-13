import sys
import unittest
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.web_lifecycle import WebLifecycle


class WebLifecycleTest(unittest.TestCase):
    def test_focus_lost_pauses_runtime(self):
        lifecycle = WebLifecycle()
        event = pygame.event.Event(pygame.WINDOWFOCUSLOST)

        lifecycle.consume(event)

        self.assertTrue(lifecycle.is_paused)

    def test_focus_gained_resumes_runtime(self):
        lifecycle = WebLifecycle()
        lifecycle.consume(pygame.event.Event(pygame.WINDOWFOCUSLOST))

        lifecycle.consume(pygame.event.Event(pygame.WINDOWFOCUSGAINED))

        self.assertFalse(lifecycle.is_paused)

