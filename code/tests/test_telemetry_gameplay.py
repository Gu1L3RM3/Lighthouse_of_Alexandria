"""Research events recorded by gameplay systems: bombs, deaths, validators, the circuit editor."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitElement, ElementKind
from core.circuit_tools.numeric_solver import SingularCircuitError
from core.components.animation_sprite import AnimateSprite
from core.components.position import Position
from core.ecs import Entity
from core.managers.bomb_manager import BombManager
from core.settings import GENERIC_LEVEL_BOMB_EDITOR_FILE
from core.systems.circuit_validators.circuit_validator_system import CircuitValidatorSystem
from core.systems.circuit_validators.resistor_association_validator_system import ResistorAssociationValidatorSystem
from core.systems.generic_level_bomb_system import GenericLevelBombSystem
from core.telemetry import TelemetryService
from core.telemetry.panel_status import PanelStatusReporter
from telemetry_fakes import FakeClock, events_of, install_memory_telemetry
from test_circuit_editor_in_memory import _Mapper, _Repository, make_system


class FakeAudio:
    def play_ui(self, *args, **kwargs):
        pass

    def play_sfx(self, *args, **kwargs):
        pass


class FakeCamera:
    def start_shake(self, **kwargs):
        pass


class FakeTileMap:
    tile_width = 16
    tile_height = 16


class FakeWebs:
    def destroy_traps_in_radius(self, entity_mn, center, radius):
        return 2


class FakeEntities:
    def __init__(self, player=None, entities=()):
        self.player = player
        self.entities = list(entities)

    def get_player(self):
        return self.player

    def get_entities_with(self, *components):
        return []

    def get_entities_by_class(self, entity_class):
        return list(self.entities)


class FakeDeathFlow:
    def __init__(self):
        self.causes = []

    def handle_player_death(self, duration=0.5, cause="unknown"):
        self.causes.append(cause)


class FakeBombScene:
    def __init__(self, bombs=1):
        self.bomb_manager = BombManager(bombs_per_level=bombs)
        self.audio_manager = FakeAudio()
        self.camera = FakeCamera()
        self.player = Entity()
        self.player.add(Position(320, 160))
        self.tile_map = FakeTileMap()
        self.pending_bombs = []
        self.active_explosions = []
        self.spider_web_system = FakeWebs()
        self.entity_mn = FakeEntities()
        self.death_flow_manager = FakeDeathFlow()
        self.player_dead_by_enemy = False


class TelemetryTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.telemetry = install_memory_telemetry(self.clock)

    def tearDown(self):
        TelemetryService.reset()


class BombSystemTelemetryTest(TelemetryTestCase):
    def make_system(self, bombs=1):
        system = GenericLevelBombSystem(FakeBombScene(bombs), circuit_service=object())
        system.sync_bomb_runtime = lambda: None
        return system

    def test_placed_bomb_reports_its_parameters_and_tile(self):
        system = self.make_system()

        system.place_bomb()

        placed = events_of(self.telemetry, "bomb_placed")
        self.assertEqual(len(placed), 1)
        self.assertEqual((placed[0]["remaining"], placed[0]["tile_x"], placed[0]["tile_y"]), (0, 20, 10))

    def test_placing_without_bombs_reports_unavailable(self):
        self.make_system(bombs=0).place_bomb()

        self.assertEqual(events_of(self.telemetry, "bomb_unavailable"), [{}])

    def test_explosion_reports_what_it_hit(self):
        system = self.make_system()

        system.explode_bomb({"center": pygame.Vector2(0, 0), "radius": 50.0, "damage": 10.0})

        self.assertEqual(
            events_of(self.telemetry, "bomb_exploded"),
            [{"enemies_hit": 0, "enemies_killed": 0, "webs_destroyed": 2, "self_hit": False}],
        )

    def test_own_bomb_death_names_its_cause(self):
        system = self.make_system()

        system.trigger_player_death()

        self.assertEqual(system.scene.death_flow_manager.causes, ["own_bomb"])


class DeathCauseTest(TelemetryTestCase):
    def test_enemy_touch_death_names_its_cause(self):
        from scenes.fases.generic_level_3 import GenericLevel3

        level = GenericLevel3.__new__(GenericLevel3)
        level.player_dead_by_enemy = False
        level.phantom_ai_system = type("Phantoms", (), {"set_touch_triggered": lambda self, value: None})()
        level.entity_mn = FakeEntities(player=None)
        level.death_flow_manager = FakeDeathFlow()

        level.on_player_touched_enemy({})

        self.assertEqual(level.death_flow_manager.causes, ["enemy"])

    def test_fall_death_names_its_cause(self):
        from scenes.fases.generic_levels import BaseGenericLevel

        level = BaseGenericLevel.__new__(BaseGenericLevel)
        level.audio_manager = FakeAudio()
        level.death_flow_manager = FakeDeathFlow()
        level.player = Entity()
        animation = AnimateSprite.__new__(AnimateSprite)
        animation.play = lambda *args, on_finish=None, **kwargs: on_finish()
        level.player.add(animation)

        level.fall_player({})

        self.assertEqual(level.death_flow_manager.causes, ["fall"])


class FakePanel:
    def __init__(self, solution_value, solution_type="voltage"):
        self.done = False
        self.active = True
        self.pannel_id = 1
        self.name_file = "generic_levels_3/fase_3/pannel1"
        self.solution_type = solution_type
        self.solution_value = solution_value
        self.solved = False

    def action(self):
        self.solved = True


class FakeCircuitValues:
    def __init__(self, circuit_values=None, total_values=None):
        self.circuit_values = circuit_values
        self.total_values = total_values

    def get_circuit_values(self, name):
        return self.circuit_values

    def get_total_values(self, name):
        return self.total_values


class ValidatorTelemetryTest(TelemetryTestCase):
    def test_validator_reports_solved_status_with_measurement(self):
        validator = CircuitValidatorSystem("generic_levels_3/fase_3", tolerance_percent=5, circuit_service=object())
        validator.circuit_manager = FakeCircuitValues({"R1": {"voltage": {"value": 5.0}}})

        validator.update(FakeEntities(entities=[FakePanel(5.0)]), 1.0)

        self.assertEqual(
            events_of(self.telemetry, "panel_status"),
            [{
                "panel_id": 1,
                "panel_file": "generic_levels_3/fase_3/pannel1",
                "status": "solved",
                "measured": 5.0,
                "expected": 5.0,
                "tolerance_percent": 5,
                "solution_type": "voltage",
            }],
        )

    def test_association_validator_reports_wrong_answer(self):
        validator = ResistorAssociationValidatorSystem("generic_levels_5/fase_5", tolerance_percent=2, circuit_service=object())
        validator.circuit_manager = FakeCircuitValues({"R1": {}}, {"resistance": {"value": 100.0}})

        validator.update(FakeEntities(entities=[FakePanel(150.0, "resistance")]), 1.0)

        statuses = events_of(self.telemetry, "panel_status")
        self.assertEqual([(status["status"], status["measured"], status["expected"]) for status in statuses],
                         [("wrong_answer", 100.0, 150.0)])

    def test_repeated_status_is_reported_once(self):
        reporter = PanelStatusReporter("generic_levels_3/fase_3", 5)

        reporter.report(1, "waiting_circuit_data")
        reporter.report(1, "waiting_circuit_data")

        self.assertEqual(len(events_of(self.telemetry, "panel_status")), 1)


def resistor_document():
    return CircuitDocument(elements=(
        CircuitElement(kind=ElementKind.RESISTOR, x=0, y=0, name="R1", value="1k"),
        CircuitElement(kind=ElementKind.VOLTAGE_SOURCE, x=64, y=0, name="V1", value="5"),
    ))


class _FailingBuilder:
    def build(self, document):
        raise SingularCircuitError("floating node")


class CircuitSubmitTelemetryTest(TelemetryTestCase):
    def test_submit_reports_components_and_solvability(self):
        system = make_system(_Repository())
        system.circuit_mapper = _Mapper(resistor_document())

        system.save_circuit()

        submit = events_of(self.telemetry, "circuit_submit")[0]
        self.assertEqual(
            (submit["panel_file"], submit["solvable"], submit["error_kind"], submit["resistor_values"]),
            ("test/panel", True, None, ["1k"]),
        )
        self.assertEqual(submit["component_counts"], {"resistor": 1, "voltage_source": 1})

    def test_unsolvable_submit_names_the_error_kind(self):
        system = make_system(_Repository())
        system.graph_builder = _FailingBuilder()

        system.save_circuit()

        submit = events_of(self.telemetry, "circuit_submit")[0]
        self.assertEqual((submit["solvable"], submit["error_kind"]), (False, "SingularCircuitError"))

    def test_submit_reports_edits_since_the_editor_opened(self):
        system = make_system(_Repository())
        system.clear_all()

        system.save_circuit()

        self.assertEqual(
            events_of(self.telemetry, "circuit_submit")[0]["edits"],
            {"placed": 0, "deleted": 0, "rotated": 0, "cleared": 1},
        )


class CircuitEditorInfoTest(unittest.TestCase):
    def make_editor(self, file):
        from scenes.circuit_editor import CircuitEditor

        editor = CircuitEditor.__new__(CircuitEditor)
        editor.file = file
        editor.input_system = type("Input", (), {"saved": True})()
        return editor

    def test_panel_editor_describes_its_file_and_save(self):
        info = self.make_editor("generic_levels_3/fase_3/pannel1").telemetry_editor_info()

        self.assertEqual(info, {"panel_file": "generic_levels_3/fase_3/pannel1", "kind": "panel", "saved": True})

    def test_bomb_editor_is_reported_as_bomb(self):
        self.assertEqual(self.make_editor(GENERIC_LEVEL_BOMB_EDITOR_FILE).telemetry_editor_info()["kind"], "bomb")


class _FadeRecorder:
    active_scene_name = "fase_8"

    def __init__(self):
        self.fades = []

    def start_fade(self, name, duration=0.5):
        self.fades.append(name)


class _PanelState:
    def set_done(self, done):
        pass


class FinalLevelTelemetryTest(TelemetryTestCase):
    def make_level(self, panels):
        from scenes.fases.final_level import FinalLevel

        level = FinalLevel.__new__(FinalLevel)
        level.entity_mn = FakeEntities(entities=panels)
        level.scene_manager = _FadeRecorder()
        level._won = False
        level.panel_timers = {}
        return level

    def test_all_panels_solved_completes_the_level_once(self):
        panel = FakePanel(1.0)
        panel.done = True
        level = self.make_level([panel])

        level._update_panel_timers(0.1)
        level._update_panel_timers(0.1)

        self.assertEqual(
            events_of(self.telemetry, "level_complete"),
            [{"scene": "fase_8", "next_scene": "ending_lighthouse"}],
        )

    def test_expired_panel_is_reported_as_reverted(self):
        panel = FakePanel(1.0)
        panel.done = True
        panel.component_for_area = 1
        panel.panel_status = _PanelState()
        level = self.make_level([panel])
        for step in ("_respawn_components_for_area", "_restore_panel_json", "_force_panel_target_resistor",
                     "_reroll_panel_area", "_stabilize_after_panel_reset"):
            setattr(level, step, lambda *args: None)
        level.circuit_manager = type("Circuits", (), {"clear_circuit": lambda self, name: None})()

        level._reset_panel(panel)

        self.assertEqual(
            events_of(self.telemetry, "panel_reverted"),
            [{"panel_id": 1, "panel_file": "generic_levels_3/fase_3/pannel1"}],
        )


if __name__ == "__main__":
    unittest.main()
