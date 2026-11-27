import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.telemetry import TelemetryService
from core.telemetry.session_tracker import SessionTracker, scene_category
from telemetry_fakes import FakeClock, events_of, install_memory_telemetry


class FakeEditor:
    def __init__(self, panel_file="generic_levels_3/fase_3/pannel1", saved=False):
        self.panel_file = panel_file
        self.saved = saved

    def telemetry_editor_info(self):
        return {"panel_file": self.panel_file, "kind": "panel", "saved": self.saved}


LEVEL = object()


class SceneCategoryTest(unittest.TestCase):
    def test_categories_follow_scene_names(self):
        cases = {
            "main_menu": "menu",
            "help": "menu",
            "home_scene": "intro",
            "level_1": "story",
            "exp_fase_4": "explanation",
            "fase_3": "puzzle",
            "death_transition": "cutscene",
            "ending_lighthouse": "cutscene",
            "circuit_editor_boot": "editor",
        }

        self.assertEqual({name: scene_category(name) for name in cases}, cases)


class SessionTrackerTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.telemetry = install_memory_telemetry(self.clock)
        # Test frames jump many seconds; only the cap test uses the default frame-gap cap.
        self.tracker = SessionTracker(self.telemetry, idle_threshold_ms=60_000, max_frame_gap_ms=120_000)

    def tearDown(self):
        TelemetryService.reset()

    def frame(self, seconds, scene_name="fase_3", scene=LEVEL, had_input=False, source="keyboard"):
        self.clock.advance(seconds)
        self.tracker.observe_frame(scene_name, scene, had_input, source)

    def test_first_frame_enters_the_scene(self):
        self.frame(0, "main_menu")

        self.assertEqual(events_of(self.telemetry, "scene_enter"), [{"scene": "main_menu", "category": "menu"}])

    def test_scene_change_reports_exit_with_duration(self):
        self.frame(0, "main_menu", had_input=True)
        self.frame(3, "main_menu")
        self.frame(1, "fase_3")

        self.assertEqual(
            events_of(self.telemetry, "scene_exit"),
            [{"scene": "main_menu", "category": "menu", "duration_ms": 4000, "active_ms": 4000}],
        )

    def test_idle_starts_after_threshold_without_input(self):
        self.frame(0, had_input=True)
        self.frame(59)
        self.assertEqual(events_of(self.telemetry, "idle_start"), [])

        self.frame(1)

        self.assertEqual(len(events_of(self.telemetry, "idle_start")), 1)

    def test_input_ends_idle_with_its_length(self):
        self.frame(0, had_input=True)
        self.frame(60)
        self.frame(4, had_input=True)

        self.assertEqual(events_of(self.telemetry, "idle_end"), [{"idle_ms": 4000}])

    def test_active_time_excludes_idle(self):
        self.frame(0, had_input=True)
        self.frame(60)
        self.frame(4)
        self.frame(1, had_input=True)
        self.frame(2, "main_menu")

        self.assertEqual(events_of(self.telemetry, "scene_exit")[0]["active_ms"], 62_000)

    def test_active_time_excludes_hidden_page(self):
        self.frame(0, had_input=True)
        self.tracker.observe_visibility("hidden")
        self.frame(5, had_input=True)
        self.tracker.observe_visibility("visible")
        self.frame(1, "main_menu", had_input=True)

        self.assertEqual(events_of(self.telemetry, "scene_exit")[0]["active_ms"], 1000)

    def test_visibility_change_is_recorded_once(self):
        self.tracker.observe_visibility("hidden")
        self.tracker.observe_visibility("hidden")

        self.assertEqual(events_of(self.telemetry, "visibility"), [{"state": "hidden"}])

    def test_unreadable_visibility_is_ignored(self):
        self.tracker.observe_visibility(None)

        self.assertEqual(events_of(self.telemetry, "visibility"), [])

    def test_long_frame_gap_counts_only_up_to_a_cap(self):
        self.tracker = SessionTracker(self.telemetry)
        self.frame(0, had_input=True)
        self.frame(30, had_input=True)
        self.frame(0, "main_menu")

        self.assertLess(events_of(self.telemetry, "scene_exit")[0]["active_ms"], 30_000)

    def test_input_source_change_is_recorded(self):
        self.frame(0, source="keyboard")
        self.frame(1, source="touch")

        self.assertEqual(events_of(self.telemetry, "input_source_change"), [{"source": "touch"}])

    def test_editor_open_and_close_with_duration_and_saved_flag(self):
        editor = FakeEditor()
        self.frame(0)
        self.frame(1, scene=editor)
        editor.saved = True
        self.frame(7, scene=LEVEL)

        self.assertEqual(
            events_of(self.telemetry, "editor_open"),
            [{"panel_file": "generic_levels_3/fase_3/pannel1", "kind": "panel"}],
        )
        self.assertEqual(
            events_of(self.telemetry, "editor_close"),
            [{
                "panel_file": "generic_levels_3/fase_3/pannel1",
                "kind": "panel",
                "duration_ms": 7000,
                "active_ms": 7000,
                "saved": True,
            }],
        )

    def test_editor_active_time_excludes_hidden_page(self):
        editor = FakeEditor()
        self.frame(0, had_input=True)
        self.frame(1, scene=editor, had_input=True)
        self.tracker.observe_visibility("hidden")
        self.frame(4, scene=editor, had_input=True)
        self.tracker.observe_visibility("visible")
        self.frame(2, scene=LEVEL, had_input=True)

        self.assertEqual(events_of(self.telemetry, "editor_close")[0]["active_ms"], 2000)

    def test_finish_closes_the_editor_before_the_scene_and_session(self):
        self.frame(0)
        self.frame(1, scene=FakeEditor())

        self.tracker.finish()

        closing = [event["type"] for event in self.telemetry.pending()][-3:]
        self.assertEqual(closing, ["editor_close", "scene_exit", "session_end"])

    def test_editor_on_the_same_scene_name_does_not_exit_the_level(self):
        self.frame(0)
        self.frame(1, scene=FakeEditor())
        self.frame(1, scene=LEVEL)

        self.assertEqual(events_of(self.telemetry, "scene_exit"), [])

    def test_finish_closes_the_scene_and_ends_the_session(self):
        self.frame(0, had_input=True)
        self.frame(2)

        self.tracker.finish()

        self.assertEqual(len(events_of(self.telemetry, "scene_exit")), 1)
        self.assertEqual(events_of(self.telemetry, "session_end"), [{"duration_ms": 2000, "active_ms": 2000}])


if __name__ == "__main__":
    unittest.main()
