"""One test per research event recorded by game code (see docs/agents/telemetry.md)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from core.components.position import Position
from core.ecs import Entity
from core.managers.bomb_manager import BombManager
from core.managers.death_flow_manager import DeathFlowManager
from core.managers.event_manager import EventManager
from core.managers.language_service import LanguageService
from core.managers.scene_manager import SceneManager
from core.telemetry import TelemetryService
from core.telemetry.event_listeners import install_event_listeners
from core.telemetry.session_info import read_game_version, record_session_start
from telemetry_fakes import FakeClock, events_of, install_memory_telemetry


class FakeLives:
    def __init__(self, current=3, max_lives=10):
        self.current_lives = current
        self.max_lives = max_lives
        self.reset_calls = 0

    def lose_life(self):
        self.current_lives -= 1
        return self.current_lives

    def is_game_over(self):
        return self.current_lives <= 0

    def reset_lives(self):
        self.reset_calls += 1
        self.current_lives = self.max_lives


class FakeTileMap:
    tile_width = 16
    tile_height = 16


class FakeLevelScene:
    def __init__(self):
        self.player = Entity()
        self.player.add(Position(40, 70))
        self.tile_map = FakeTileMap()


class FakeSceneManager:
    def __init__(self, scene_name="fase_3", scene=None):
        self.active_scene_name = scene_name
        self.active_scene = scene
        self.fades = []
        self.journeys = []

    def start_fade(self, name, duration=0.5):
        self.fades.append(name)

    def start_new_journey(self, start_scene_name="home_scene", duration=0.6):
        self.journeys.append(start_scene_name)

    def has_scene(self, name):
        return True

    def get_scene(self, name):
        return object()

    def replace_scene_and_fade(self, name, scene, duration=0.5):
        self.fades.append(name)

    def can_resume_scene(self):
        return False


class FakeSceneFactory:
    def recreate(self, scene):
        return scene


class FakeSave:
    def autosave_scene(self, *args, **kwargs):
        pass

    def clear_save(self):
        pass


class TelemetryTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.telemetry = install_memory_telemetry(self.clock)

    def tearDown(self):
        TelemetryService.reset()


def make_death_flow(lives):
    flow = DeathFlowManager.__new__(DeathFlowManager)
    flow.life_manager = lives
    flow.scene_manager = FakeSceneManager(scene=FakeLevelScene())
    flow.scene_factory = FakeSceneFactory()
    flow.save_manager = FakeSave()
    flow.death_scene_name = "death_transition"
    flow.game_over_return_scene = "level_2"
    flow.death_context = None
    return flow


class DeathFlowTelemetryTest(TelemetryTestCase):
    def test_player_death_reports_cause_lives_and_tile(self):
        flow = make_death_flow(FakeLives(current=3))

        flow.handle_player_death(cause="fall")

        self.assertEqual(
            events_of(self.telemetry, "player_death"),
            [{"cause": "fall", "lives_before": 3, "lives_after": 2, "game_over": False, "tile_x": 2, "tile_y": 4}],
        )

    def test_last_life_reports_game_over(self):
        flow = make_death_flow(FakeLives(current=1))
        flow.handle_player_death(cause="enemy")

        flow.resolve_death_transition()

        self.assertEqual(events_of(self.telemetry, "game_over"), [{"scene": "fase_3", "return_scene": "level_2"}])

    def test_remaining_life_reports_level_retry(self):
        flow = make_death_flow(FakeLives(current=3))
        flow.handle_player_death(cause="own_bomb")

        flow.resolve_death_transition()

        self.assertEqual(events_of(self.telemetry, "level_retry"), [{"scene": "fase_3", "lives": 2}])


class SceneManagerTelemetryTest(TelemetryTestCase):
    def setUp(self):
        super().setUp()
        self.manager = SceneManager()
        for name in ("fase_3", "main_menu", "help"):
            self.manager.register(name, _StubScene())
        self.manager.change("fase_3")

    def _finish_transition(self):
        while self.manager.transitioning:
            self.manager.update_transition()

    def test_pause_close_reports_how_long_the_menu_was_open(self):
        self.manager.open_menu()
        self._finish_transition()
        self.clock.advance(6)

        self.manager.resume_from_menu()

        self.assertEqual(len(events_of(self.telemetry, "pause_open")), 1)
        self.assertEqual(events_of(self.telemetry, "pause_close"), [{"duration_ms": 6000}])

    def test_help_close_reports_how_long_help_was_open(self):
        self.manager.open_help()
        self._finish_transition()
        self.clock.advance(2)

        self.manager.resume_from_help()

        self.assertEqual(len(events_of(self.telemetry, "help_open")), 1)
        self.assertEqual(events_of(self.telemetry, "help_close"), [{"duration_ms": 2000}])


class _StubScene:
    def __init__(self):
        self.screen = pygame.Surface((4, 4))

    def start(self):
        pass

    def end(self):
        pass


class _MemoryLanguageRepository:
    def __init__(self):
        self.language = "pt-BR"

    def load_language(self):
        return self.language

    def save_language(self, language):
        self.language = language


class LanguageTelemetryTest(TelemetryTestCase):
    def test_language_change_reports_both_languages(self):
        service = LanguageService(repository=_MemoryLanguageRepository())

        service.toggle_language()

        self.assertEqual(events_of(self.telemetry, "language_change"), [{"from": "pt-BR", "to": "en"}])

    def test_setting_the_same_language_reports_nothing(self):
        service = LanguageService(repository=_MemoryLanguageRepository())

        service.set_language("pt-BR")

        self.assertEqual(events_of(self.telemetry, "language_change"), [])


def resistor_results(voltage, current):
    return {"R1": {"voltage": {"value": voltage}, "current": {"value": current}}}


class BombManagerTelemetryTest(TelemetryTestCase):
    def test_new_calibration_is_reported_once(self):
        bombs = BombManager()

        bombs.update_from_resistor_results(resistor_results(5.0, 0.05))
        bombs.update_from_resistor_results(resistor_results(5.0, 0.05))

        calibrations = events_of(self.telemetry, "bomb_calibrated")
        self.assertEqual(len(calibrations), 1)
        self.assertEqual(
            sorted(calibrations[0]),
            ["current_r1", "damage", "explosion_delay", "explosion_radius", "used_fallback", "voltage_r1"],
        )
        self.assertFalse(calibrations[0]["used_fallback"])


class DoorTelemetryTest(TelemetryTestCase):
    def setUp(self):
        super().setUp()
        self._previous_scene_manager = SceneManager._instance
        self.scene_manager = FakeSceneManager("fase_3")
        SceneManager._instance = self.scene_manager

    def tearDown(self):
        SceneManager._instance = self._previous_scene_manager
        super().tearDown()

    def test_entering_the_door_completes_the_level(self):
        from entities.animated_tiles.door import Door

        door = Door.__new__(Door)
        door.next_scene = "exp_fase_4"
        door.can_player_interact = lambda player: True

        door.try_enter(None)

        self.assertEqual(
            events_of(self.telemetry, "level_complete"),
            [{"scene": "fase_3", "next_scene": "exp_fase_4"}],
        )


class _PanelStatus:
    def set_done(self, done):
        self.done = done


class ControlPanelTelemetryTest(TelemetryTestCase):
    def test_solved_panel_reports_its_circuit_file(self):
        from entities.itens.control_pannel import ControlPannel

        events = EventManager()
        install_event_listeners(events, self.telemetry)
        panel = ControlPannel.__new__(ControlPannel)
        panel.event_manager = events
        panel.action_type = "pannel_door1"
        panel.stealth_bonus_enabled = False
        panel.stealth_bonus_duration = 0
        panel.bomb_reward = 0
        panel.pannel_id = 1
        panel.name_file = "generic_levels_3/fase_3/pannel1"
        panel.panel_status = _PanelStatus()

        panel.action()

        self.assertEqual(
            events_of(self.telemetry, "panel_solved"),
            [{"panel_id": 1, "panel_file": "generic_levels_3/fase_3/pannel1"}],
        )


class _SaveWithGame(FakeSave):
    def load_game(self):
        return {"current_scene": "fase_4", "lives": {"current": 5, "max": 10}}


class _LivesState(FakeLives):
    def set_state(self, current_lives, max_lives):
        self.current_lives = current_lives


class MainMenuTelemetryTest(TelemetryTestCase):
    def make_menu(self):
        from scenes.main_menu_scene import MainMenuScene

        menu = MainMenuScene.__new__(MainMenuScene)
        menu.save_manager = _SaveWithGame()
        menu.life_manager = _LivesState()
        menu.scene_manager = FakeSceneManager("main_menu")
        return menu

    def test_start_new_game_is_recorded(self):
        self.make_menu().start_new_game()

        self.assertEqual(events_of(self.telemetry, "new_game"), [{}])

    def test_continue_from_save_names_the_saved_scene(self):
        self.make_menu().resume_current_scene()

        self.assertEqual(events_of(self.telemetry, "continue_game"), [{"scene": "fase_4", "from_save": True}])


class SessionInfoTest(TelemetryTestCase):
    def test_session_start_describes_the_platform(self):
        record_session_start(
            self.telemetry,
            game_version="0.4.0",
            language="en",
            is_web=True,
            viewport=(1366, 768),
            input_source="touch",
        )

        self.assertEqual(
            events_of(self.telemetry, "session_start"),
            [{
                "game_version": "0.4.0",
                "language": "en",
                "platform": "web",
                "viewport_w": 1366,
                "viewport_h": 768,
                "input_source": "touch",
            }],
        )

    def test_game_version_reads_version_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "VERSION").write_text("0.4.0\n", encoding="utf-8")

            self.assertEqual(read_game_version([Path(tmp)]), "0.4.0")

    def test_game_version_defaults_to_dev(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_game_version([Path(tmp)]), "dev")


if __name__ == "__main__":
    unittest.main()
