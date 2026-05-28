import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.components.area_trigger import AreaTrigger
from core.components.position import Position
from core.managers.event_manager import EventManager
from entities.animated_tiles.fall_ground import FallGround
from entities.player import Player


class _FakeResourceManager:
    def __init__(self):
        frame = pygame.Surface((16, 16), pygame.SRCALPHA)
        self._sheet = {"broken": [frame], "idle": [frame]}

    def load_sprite_sheet(self, *_args, **_kwargs):
        return self._sheet


class _FakeAudioManager:
    def __init__(self):
        self.calls: list[tuple[str, float]] = []

    def play_sfx(self, filename: str, volume: float = 1.0):
        self.calls.append((filename, volume))


class FallGroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        EventManager.get().clear()
        FallGround._last_fall_ms = -10_000
        self.events: list[str] = []
        self.event_manager = EventManager.get()
        self.event_manager.subscribe("request_freeze", lambda event: self.events.append(event["type"]))
        self.event_manager.subscribe("fall_player", lambda event: self.events.append(event["type"]))
        self.audio_manager = _FakeAudioManager()

    def _make_player(self, x: float, y: float) -> Player:
        return Player(x, y)

    def _make_fall_ground(self) -> FallGround:
        with (
            patch("entities.animated_tiles.fall_ground.ResourceManager.get", return_value=_FakeResourceManager()),
            patch("entities.animated_tiles.fall_ground.AudioManager.get", return_value=self.audio_manager),
        ):
            return FallGround(0, 0)

    def test_does_not_trigger_when_player_only_clips_corner(self):
        ground = self._make_fall_ground()
        player = self._make_player(11, 0)

        ground.on_entered(player)

        self.assertEqual([], self.events)
        self.assertEqual([], self.audio_manager.calls)
        self.assertTrue(ground.get(AreaTrigger).active)

    def test_plays_warning_sound_before_posting_fall_events(self):
        ground = self._make_fall_ground()
        player = self._make_player(4, 0)

        with patch("entities.animated_tiles.fall_ground.pygame.time.get_ticks", side_effect=[1000, 1100, 1100]):
            ground.on_entered(player)
            ground.on_stayed(player)

        self.assertEqual(["request_freeze", "fall_player"], self.events)
        self.assertEqual(1, len(self.audio_manager.calls))
        self.assertFalse(ground.get(AreaTrigger).active)

    def test_leaving_before_delay_cancels_pending_fall(self):
        ground = self._make_fall_ground()
        player = self._make_player(4, 0)

        with patch("entities.animated_tiles.fall_ground.pygame.time.get_ticks", return_value=1000):
            ground.on_entered(player)

        player.get(Position).x = 40
        ground.on_exit(player)

        player.get(Position).x = 4
        with patch("entities.animated_tiles.fall_ground.pygame.time.get_ticks", side_effect=[1050, 1160, 1160]):
            ground.on_entered(player)
            ground.on_stayed(player)

        self.assertEqual(["request_freeze", "fall_player"], self.events)
        self.assertEqual(2, len(self.audio_manager.calls))


if __name__ == "__main__":
    unittest.main()
