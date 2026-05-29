import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Vector2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.components.collider import Collider
from core.components.freeze import Freeze
from core.components.phantom_ai import PhantomAI
from core.components.position import Position
from core.components.team import Team
from core.components.velocity import Velocity
from core.ecs import Entity
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from core.systems.enemy_touch_game_over_system import EnemyTouchGameOverSystem
from core.systems.generic_level_ghost_system import GenericLevelGhostSystem
from core.systems.phantom_ai_system import PhantomAISystem


class _FakeAudioManager:
    def __init__(self):
        self.calls: list[tuple[str, float]] = []

    def play_sfx(self, filename: str, volume: float = 1.0):
        self.calls.append((filename, volume))


class _DummyPlayer(Entity):
    def __init__(self, x: float, y: float, external_speed_multiplier: float = 1.0):
        super().__init__()
        self._external_speed_multiplier = external_speed_multiplier
        self.add(Position(x, y), Velocity(0, 0), Collider(8, 6), Freeze(), Team("player"))

    def get_external_speed_multiplier(self) -> float:
        return float(self._external_speed_multiplier)


class _DummyTileMap:
    map_width = 2048
    map_height = 2048
    tile_width = 16
    tile_height = 16

    def __init__(self):
        self.pathfinder = SimpleNamespace(find_path=lambda _start, _target: [])

    def get_tile_from_position(self, pos: Position) -> tuple[int, int]:
        return int(pos.x // self.tile_width), int(pos.y // self.tile_height)


class PhantomFairnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        EventManager.get().clear()

    def _make_phantom(self, x: float, y: float, *, detection_radius: float = 120.0, touch_radius: float = 10.0, chase_speed: float = 62.0) -> Entity:
        phantom = Entity()
        phantom.add(
            Position(x, y),
            Velocity(0, 0),
            Collider(10, 8),
            Team("enemy"),
            PhantomAI(
                detection_radius=detection_radius,
                touch_radius=touch_radius,
                chase_speed=chase_speed,
                patrol_speed=38.0,
                route=[],
            ),
        )
        return phantom

    def test_phantom_collision_is_ignored_by_enemy_touch_system(self):
        entity_manager = EntityManager()
        player = _DummyPlayer(0, 0)
        phantom = self._make_phantom(0, 0)
        entity_manager.add_entity(player)
        entity_manager.add_entity(phantom)
        entity_manager.get_player = lambda: player

        events: list[str] = []
        EventManager.get().subscribe("player_touched_enemy", lambda event: events.append(event["type"]))

        system = EnemyTouchGameOverSystem()
        system.update(entity_manager, 0.016)

        self.assertEqual([], events)
        self.assertFalse(system.triggered)

    def test_chase_start_plays_warning_sound_once(self):
        entity_manager = EntityManager()
        player = _DummyPlayer(80, 80)
        phantom = self._make_phantom(64, 64, detection_radius=120.0)
        entity_manager.add_entity(phantom)
        entity_manager.get_player = lambda: player

        audio = _FakeAudioManager()
        with patch("core.systems.phantom_ai_system.AudioManager.get", return_value=audio):
            system = PhantomAISystem(_DummyTileMap())

        system.update(entity_manager, 0.016)
        system.update(entity_manager, 0.016)

        self.assertEqual(1, len(audio.calls))
        self.assertEqual("sfx/phantom_chase_start.wav", audio.calls[0][0])

    def test_overload_does_not_increase_chase_speed(self):
        overloaded_player = _DummyPlayer(160, 160, external_speed_multiplier=0.35)
        normal_player = _DummyPlayer(160, 160, external_speed_multiplier=1.0)
        phantom_overloaded = self._make_phantom(64, 64)
        phantom_normal = self._make_phantom(64, 64)

        audio = _FakeAudioManager()
        with patch("core.systems.phantom_ai_system.AudioManager.get", return_value=audio):
            system = PhantomAISystem(_DummyTileMap())

        phantom_overloaded.get(PhantomAI).state = PhantomAI.STATE_CHASE
        phantom_normal.get(PhantomAI).state = PhantomAI.STATE_CHASE

        system._chase_player(phantom_overloaded, phantom_overloaded.get(PhantomAI), overloaded_player, overloaded_player.get(Position).center_pos())
        overloaded_speed = Vector2(phantom_overloaded.get(Velocity).vel).length()

        system._chase_player(phantom_normal, phantom_normal.get(PhantomAI), normal_player, normal_player.get(Position).center_pos())
        normal_speed = Vector2(phantom_normal.get(Velocity).vel).length()

        self.assertAlmostEqual(normal_speed, overloaded_speed, places=4)

    def test_ghost_respawn_uses_original_spawn_instead_of_death_position(self):
        spawned: list[dict] = []
        fake_scene = SimpleNamespace(
            _ghost_spawn_templates={
                "phantom_spawn_0": {
                    "enemy_type": "phantom",
                    "x": 128.0,
                    "y": 192.0,
                    "props": {},
                    "route": [],
                    "pending_respawn": False,
                    "active_entity_id": None,
                }
            },
            _ghost_entity_to_spawn_key={5: "phantom_spawn_0"},
            ghost_respawn_queue=[],
            ghost_rebirth_effects=[],
            entity_mn=SimpleNamespace(add_entity=lambda enemy: spawned.append(enemy)),
            audio_manager=_FakeAudioManager(),
        )
        system = GenericLevelGhostSystem(fake_scene)

        system.queue_ghost_respawn_by_entity_id(5, death_x=400.0, death_y=500.0)
        queued = fake_scene.ghost_respawn_queue[0]
        self.assertIsNone(queued["respawn_x"])
        self.assertIsNone(queued["respawn_y"])

        with patch(
            "core.systems.generic_level_ghost_system.EnemyFactory.create",
            side_effect=lambda **kwargs: SimpleNamespace(id=99, **kwargs),
        ):
            system.start_ghost_rebirth_effect("phantom_spawn_0", respawn_x=queued["respawn_x"], respawn_y=queued["respawn_y"])
            effect = fake_scene.ghost_rebirth_effects[0]
            self.assertEqual(128.0, effect["x"])
            self.assertEqual(192.0, effect["y"])

            effect["elapsed"] = effect["duration"]
            system.update_ghost_rebirth_effects(0.0)

        self.assertEqual(128.0, spawned[0].x)
        self.assertEqual(192.0, spawned[0].y)


if __name__ == "__main__":
    unittest.main()
