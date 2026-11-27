import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitElement, ElementKind
from core.telemetry import TelemetryService
from core.telemetry.circuit_summary import EditTally, summarize_circuit
from core.telemetry.slides import SlideTracker
from telemetry_fakes import FakeClock, events_of, install_memory_telemetry


def element(kind, name=None, value=None, x=0):
    return CircuitElement(kind=kind, x=x, y=0, name=name, value=value)


class CircuitSummaryTest(unittest.TestCase):
    def test_summary_counts_components_and_lists_values(self):
        document = CircuitDocument(elements=(
            element(ElementKind.RESISTOR, "R1", "10k", x=0),
            element(ElementKind.RESISTOR, "R2", "1k", x=64),
            element(ElementKind.VOLTAGE_SOURCE, "V1", "5", x=128),
            element(ElementKind.WIRE, x=192),
        ))

        self.assertEqual(
            summarize_circuit(document),
            {
                "component_counts": {"resistor": 2, "voltage_source": 1, "wire": 1},
                "resistor_values": ["10k", "1k"],
                "source_values": {"voltage_source": ["5"]},
            },
        )

    def test_edit_tally_counts_each_kind_of_edit(self):
        tally = EditTally()
        tally.count("placed")
        tally.count("placed")
        tally.count("rotated")

        self.assertEqual(tally.as_dict(), {"placed": 2, "deleted": 0, "rotated": 1, "cleared": 0})


class SlideTrackerTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.telemetry = install_memory_telemetry(self.clock, scene="exp_fase_3")
        self.slides = SlideTracker(self.telemetry)

    def tearDown(self):
        TelemetryService.reset()

    def test_slide_change_reports_the_previous_slide_time(self):
        self.slides.observe("lesson", 0)
        self.clock.advance(3)
        self.slides.observe("lesson", 1)

        self.assertEqual(
            events_of(self.telemetry, "explanation_slide"),
            [{"dialogue_id": "lesson", "index": 0, "duration_ms": 3000}],
        )

    def test_closing_the_slides_reports_the_last_one(self):
        self.slides.observe("lesson", 0)
        self.clock.advance(2)
        self.slides.observe(None, None)

        self.assertEqual(len(events_of(self.telemetry, "explanation_slide")), 1)

    def test_same_slide_reports_nothing(self):
        self.slides.observe("lesson", 0)
        self.slides.observe("lesson", 0)

        self.assertEqual(events_of(self.telemetry, "explanation_slide"), [])


if __name__ == "__main__":
    unittest.main()
