import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.telemetry import NullTransport, TelemetryService


class FakeClock:
    def __init__(self, seconds=100.0):
        self.seconds = seconds

    def __call__(self):
        return self.seconds


class RecordingTransport:
    enabled = True

    def __init__(self):
        self.payloads = []

    def send(self, payload: str):
        self.payloads.append(payload)

    def events(self):
        return [event for payload in self.payloads for event in json.loads(payload)]


class FailingTransport(RecordingTransport):
    def __init__(self):
        super().__init__()
        self.fail = True

    def send(self, payload: str):
        if self.fail:
            raise RuntimeError("JS bridge threw")
        super().send(payload)


def make_service(transport=None, clock=None, **kwargs):
    return TelemetryService(
        transport=transport or RecordingTransport(),
        clock=clock or FakeClock(),
        wall_clock=lambda: datetime(2026, 1, 2, 3, 4, 5, 678000, tzinfo=timezone.utc),
        session_id="abc123",
        scene_provider=lambda: "fase_3",
        **kwargs,
    )


class TelemetryServiceTest(unittest.TestCase):
    def tearDown(self):
        TelemetryService.reset()

    def test_default_instance_uses_null_transport(self):
        self.assertIsInstance(TelemetryService.get().transport, NullTransport)

    def test_null_transport_service_queues_nothing(self):
        service = TelemetryService(transport=NullTransport())

        service.record("scene_enter", scene="x")

        self.assertEqual(service.pending(), [])

    def test_record_builds_event_envelope(self):
        clock = FakeClock(100.0)
        service = make_service(clock=clock)
        clock.seconds = 101.25

        service.record("panel_solved", panel_id=2)

        self.assertEqual(
            service.pending(),
            [{
                "v": 1,
                "seq": 1,
                "session_id": "abc123",
                "t_ms": 1250,
                "ts": "2026-01-02T03:04:05.678Z",
                "scene": "fase_3",
                "type": "panel_solved",
                "props": {"panel_id": 2},
            }],
        )

    def test_seq_increases_by_one_per_event(self):
        service = make_service()

        for _ in range(3):
            service.record("tick")

        self.assertEqual([event["seq"] for event in service.pending()], [1, 2, 3])

    def test_new_service_gets_a_uuid4_hex_session_id(self):
        service = TelemetryService(transport=RecordingTransport())

        self.assertRegex(service.session_id, r"^[0-9a-f]{32}$")

    def test_flush_sends_queued_events_as_one_json_array(self):
        transport = RecordingTransport()
        service = make_service(transport=transport)
        service.record("a")
        service.record("b")

        service.flush()

        self.assertEqual(len(transport.payloads), 1)
        self.assertEqual([event["type"] for event in transport.events()], ["a", "b"])
        self.assertEqual(service.pending(), [])

    def test_flush_with_empty_queue_sends_nothing(self):
        transport = RecordingTransport()

        make_service(transport=transport).flush()

        self.assertEqual(transport.payloads, [])

    def test_flush_caps_the_batch_size(self):
        transport = RecordingTransport()
        service = make_service(transport=transport, max_batch=2)
        for name in "abc":
            service.record(name)

        service.flush()

        self.assertEqual([event["type"] for event in transport.events()], ["a", "b"])
        self.assertEqual([event["type"] for event in service.pending()], ["c"])

    def test_flush_all_drains_every_batch(self):
        transport = RecordingTransport()
        service = make_service(transport=transport, max_batch=2)
        for name in "abcde":
            service.record(name)

        service.flush_all()

        self.assertEqual(len(transport.payloads), 3)
        self.assertEqual(service.pending(), [])

    def test_full_queue_drops_the_oldest_event(self):
        service = make_service(max_queue=2)
        for name in "abc":
            service.record(name)

        self.assertEqual([event["type"] for event in service.pending()], ["b", "c"])

    def test_dropped_count_is_reported_in_the_next_telemetry_dropped_event(self):
        transport = RecordingTransport()
        service = make_service(transport=transport, max_queue=2)
        for name in "abcd":
            service.record(name)

        service.flush_all()

        dropped = [event for event in transport.events() if event["type"] == "telemetry_dropped"]
        self.assertEqual(dropped[0]["props"], {"count": 2})

    def test_bridge_exception_is_swallowed_and_batch_retried(self):
        transport = FailingTransport()
        service = make_service(transport=transport)
        service.record("a")

        service.flush()
        transport.fail = False
        service.flush()

        self.assertEqual([event["type"] for event in transport.events()], ["a"])

    def test_non_finite_numbers_become_null(self):
        service = make_service()

        service.record("bomb_calibrated", voltage_r1=float("inf"), nested={"x": float("nan")})

        self.assertEqual(service.pending()[0]["props"], {"voltage_r1": None, "nested": {"x": None}})

    def test_failing_scene_provider_records_null_scene(self):
        def broken():
            raise AttributeError("no scene yet")

        service = TelemetryService(transport=RecordingTransport(), scene_provider=broken)

        service.record("a")

        self.assertIsNone(service.pending()[0]["scene"])

    def test_timer_returns_elapsed_ms_once(self):
        clock = FakeClock(10.0)
        service = make_service(clock=clock)
        service.start_timer("pause")
        clock.seconds = 12.5

        self.assertEqual(service.stop_timer("pause"), 2500)
        self.assertIsNone(service.stop_timer("pause"))

    def test_set_instance_replaces_the_shared_service(self):
        service = make_service()

        TelemetryService.set_instance(service)

        self.assertIs(TelemetryService.get(), service)


if __name__ == "__main__":
    unittest.main()
