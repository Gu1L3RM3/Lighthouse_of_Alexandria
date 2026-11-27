import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.ecs import Component, Entity
from core.managers.event_manager import EventManager
from core.telemetry import TelemetryService
from core.telemetry.event_listeners import install_event_listeners
from telemetry_fakes import FakeClock, events_of, install_memory_telemetry


class FakeDialogue(Component):
    def __init__(self, lines):
        self.lines = lines

    def to_dict(self):
        return {}


class NamedDialogueArea(Entity):
    def __init__(self, name, lines):
        super().__init__()
        self.name = name
        self.add(FakeDialogue(lines))


class EventListenersTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.telemetry = install_memory_telemetry(self.clock)
        self.events = EventManager()
        install_event_listeners(self.events, self.telemetry)

    def tearDown(self):
        TelemetryService.reset()

    def test_listeners_survive_scene_change_clear(self):
        self.events.clear()
        self.events.post({"type": "get_key"})

        self.assertEqual(events_of(self.telemetry, "item_collected"), [{"item": "key"}])

    def test_dialogue_end_reports_duration_and_line_count(self):
        area = NamedDialogueArea("intro_arquimedes", ["a", "b", "c"])
        self.events.post({"type": "dialogue_start", "entity": area})
        self.clock.advance(4.0)
        self.events.post({"type": "dialogue_end", "entity": area})

        self.assertEqual(
            events_of(self.telemetry, "dialogue_end"),
            [{"dialogue_id": "intro_arquimedes", "duration_ms": 4000, "lines": 3}],
        )

    def test_dialogue_start_names_unnamed_speakers_by_class(self):
        speaker = Entity()
        self.events.post({"type": "dialogue_start", "entity": speaker})

        self.assertEqual(events_of(self.telemetry, "dialogue_start"), [{"dialogue_id": "Entity", "lines": None}])

    def test_panel_solved_is_recorded(self):
        self.events.post({"type": "panel_solved", "pannel_id": 2, "panel_file": "generic_levels_3/fase_3/pannel2"})

        self.assertEqual(
            events_of(self.telemetry, "panel_solved"),
            [{"panel_id": 2, "panel_file": "generic_levels_3/fase_3/pannel2"}],
        )

    def test_resistor_pickup_is_an_item_collected(self):
        self.events.post({"type": "resistor_collected", "value": "10k", "area_id": 1, "spawn_x": 3, "spawn_y": 4})

        self.assertEqual(
            events_of(self.telemetry, "item_collected"),
            [{"item": "resistor", "value": "10k", "area_id": 1}],
        )

    def test_old_paper_close_reports_reading_time(self):
        self.events.post({"type": "open_old_paper"})
        self.clock.advance(2.5)
        self.events.post({"type": "close_old_paper"})

        self.assertEqual(events_of(self.telemetry, "old_paper_close"), [{"duration_ms": 2500}])

    def test_listener_errors_never_reach_the_game(self):
        self.events.post({"type": "dialogue_start", "entity": object()})

        self.assertEqual(len(events_of(self.telemetry, "dialogue_start")), 1)


if __name__ == "__main__":
    unittest.main()
