import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.managers.circuit_manager import CircuitManager
from core.managers.event_manager import EventManager
from core.managers.bomb_manager import BombManager
from core.managers.entity_manager import EntityManager
from core.managers.resource_manager import ResourceManager
from core.systems.generic_level_bomb_system import GenericLevelBombSystem
from core.systems.circuit_validators.circuit_validator_system import CircuitValidatorSystem
from entities.itens.control_pannel import ControlPannel


class _DummyAudioManager:
    def play_ui(self, *args, **kwargs):
        _ = (args, kwargs)

    def play_sfx(self, *args, **kwargs):
        _ = (args, kwargs)


class _DummyCamera:
    def start_shake(self, *args, **kwargs):
        _ = (args, kwargs)


class _DummyScene:
    def __init__(self):
        self.bomb_manager = BombManager(bombs_per_level=1, default_netlist_path=None)
        self.audio_manager = _DummyAudioManager()
        self.camera = _DummyCamera()
        self.pending_bombs = []
        self.active_explosions = []
        self.circuit_manager = CircuitManager.get()
        self.entity_mn = EntityManager()
        self.player = None
        self.death_flow_manager = type("_DeathFlow", (), {"handle_player_death": lambda self: None})()


class GameplayIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((32, 32))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        CircuitManager._instance = None
        EventManager._instance = None
        self.circuit_manager = CircuitManager.get()
        self.event_manager = EventManager.get()
        self.event_manager.clear()

    def _fake_load_sprite_sheet(self, *_args, **_kwargs):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        return {"idle": [surf]}

    def test_bomb_system_uses_circuit_manager_values_without_solver_fallback(self):
        scene = _DummyScene()
        scene.circuit_manager.add_circuit_values(
            "bombs/bomb_editor",
            {
                "R1": {
                    "voltage": {"value": 6.0},
                    "current": {"value": 0.03},
                }
            },
        )
        system = GenericLevelBombSystem(scene)

        system.sync_bomb_runtime()

        self.assertFalse(scene.bomb_manager.current_params.used_fallback)
        self.assertEqual(scene.bomb_manager.current_params.voltage_r1, 6.0)
        self.assertEqual(scene.bomb_manager.current_params.current_r1, 0.03)

    def test_circuit_validator_marks_panel_done_when_circuit_manager_matches_solution(self):
        triggered = {"solved": False}
        with patch.object(ResourceManager, "load_sprite_sheet", new=self._fake_load_sprite_sheet):
            panel = ControlPannel(
                0,
                0,
                True,
                {
                    "pannel_id": 1,
                    "type_solution": "voltage",
                    "target_component": "R1",
                    "component_for_area": 1,
                    "tmx_file": "generic_levels_3/fase_3",
                    "action": "porta",
                },
            )
        panel.solution_value = 10.0
        original_action = panel.action

        def tracked_action():
            triggered["solved"] = True
            original_action()

        panel.action = tracked_action

        entity_manager = EntityManager()
        entity_manager.add_entity(panel)
        self.circuit_manager.add_circuit_values(
            panel.name_file,
            {
                "R1": {
                    "voltage": {"value": 10.0},
                    "current": {"value": 0.01},
                }
            },
        )

        validator = CircuitValidatorSystem("generic_levels_3/fase_3")
        validator.update(entity_manager, 1.0)

        self.assertTrue(triggered["solved"])
        self.assertTrue(panel.done)
