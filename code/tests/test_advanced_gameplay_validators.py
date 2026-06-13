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
from core.managers.entity_manager import EntityManager
from core.managers.resource_manager import ResourceManager
from core.systems.circuit_validators.max_power_transfer_validator_system import MaxPowerTransferValidatorSystem
from core.systems.circuit_validators.resistor_pair_validator_system import ResistorPairValidatorSystem
from core.systems.circuit_validators.thevenin_norton_validator_system import TheveninNortonValidatorSystem
from entities.itens.control_pannel import ControlPannel


class AdvancedGameplayValidatorsTest(unittest.TestCase):
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

    def _make_panel(self, *, panel_id: int, solution_type: str, target_component: str, area: int):
        with patch.object(ResourceManager, "load_sprite_sheet", new=self._fake_load_sprite_sheet):
            return ControlPannel(
                0,
                0,
                True,
                {
                    "pannel_id": panel_id,
                    "type_solution": solution_type,
                    "target_component": target_component,
                    "component_for_area": area,
                    "tmx_file": "generic_levels_3/fase_3",
                    "action": "porta",
                },
            )

    def _track_panel_action(self, panel: ControlPannel):
        triggered = {"solved": False}
        original_action = panel.action

        def tracked_action():
            triggered["solved"] = True
            original_action()

        panel.action = tracked_action
        return triggered

    def test_resistor_pair_validator_marks_panel_done_when_multiple_targets_match(self):
        panel = self._make_panel(panel_id=5, solution_type="voltage", target_component="R1,R2", area=1)
        panel.solution_value = {"R1": 12.0, "R2": 5.0}
        triggered = self._track_panel_action(panel)

        entity_manager = EntityManager()
        entity_manager.add_entity(panel)
        self.circuit_manager.add_circuit_values(
            panel.name_file,
            {
                "R1": {"voltage": {"value": 12.0}, "current": {"value": 0.01}},
                "R2": {"voltage": {"value": 5.0}, "current": {"value": 0.02}},
            },
        )

        validator = ResistorPairValidatorSystem("generic_levels_3/fase_3")
        validator.update(entity_manager, 1.0)

        self.assertTrue(triggered["solved"])
        self.assertTrue(panel.done)

    def test_thevenin_norton_validator_marks_panel_done_when_expected_equivalent_matches(self):
        panel = self._make_panel(panel_id=6, solution_type="voltage", target_component="R1", area=1)
        panel.solution_value = {
            "expected": {
                "source_kind": "voltage",
                "source_label": "Vth",
                "source_value": 5.0,
                "resistance_label": "Rth",
                "resistance_value": 100.0,
            }
        }
        triggered = self._track_panel_action(panel)

        entity_manager = EntityManager()
        entity_manager.add_entity(panel)
        self.circuit_manager.add_circuit_values(
            panel.name_file,
            {"R1": {"voltage": {"value": 1.0}, "current": {"value": 0.01}}},
        )

        validator = TheveninNortonValidatorSystem("generic_levels_3/fase_3")
        with patch.object(validator, "_validate_player_topology", return_value=(True, "")), patch.object(
            validator,
            "_extract_player_equivalent_values",
            return_value=(
                {
                    "source_kind": "voltage",
                    "source_value": 5.0,
                    "resistor_value": 100.0,
                },
                "",
            ),
        ), patch.object(
            validator,
            "_load_net_components",
            return_value={
                "R1": ("n1", "n2"),
                "R2": ("n2", "n3"),
                "V1": ("n3", "n1"),
            },
        ):
            validator.update(entity_manager, 1.0)

        self.assertTrue(triggered["solved"])
        self.assertTrue(panel.done)

    def test_max_power_validator_marks_panel_done_when_circuit_manager_matches_expected(self):
        panel = self._make_panel(
            panel_id=7,
            solution_type="power;resistance;voltage;current",
            target_component="R1",
            area=1,
        )
        panel.solution_value = {
            "target": "R1",
            "answer_label": "10",
            "answer_value": 10.0,
            "vth": 20.0,
            "rth": 10.0,
            "rl": 10.0,
            "resistance": 10.0,
            "voltage": 10.0,
            "current": 1.0,
            "power": 10.0,
        }
        triggered = self._track_panel_action(panel)

        entity_manager = EntityManager()
        entity_manager.add_entity(panel)
        self.circuit_manager.add_circuit_values(
            panel.name_file,
            {
                "R1": {
                    "voltage": {"value": 10.0},
                    "current": {"value": 1.0},
                    "power": {"value": 10.0},
                }
            },
        )

        validator = MaxPowerTransferValidatorSystem("generic_levels_3/fase_3")
        validator.update(entity_manager, 1.0)

        self.assertTrue(triggered["solved"])
        self.assertTrue(panel.done)
