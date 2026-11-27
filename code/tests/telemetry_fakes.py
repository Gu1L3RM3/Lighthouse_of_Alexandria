"""Shared fakes for telemetry tests: a service that keeps events in memory."""

from datetime import datetime, timezone

from core.telemetry import TelemetryService


class FakeClock:
    def __init__(self, seconds=0.0):
        self.seconds = seconds

    def __call__(self):
        return self.seconds

    def advance(self, seconds):
        self.seconds += seconds


class MemoryTransport:
    enabled = True

    def send(self, payload):
        _ = payload


def install_memory_telemetry(clock=None, scene="fase_3"):
    """Makes TelemetryService.get() a recording service; undo with TelemetryService.reset()."""
    service = TelemetryService(
        transport=MemoryTransport(),
        clock=clock or FakeClock(),
        wall_clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        session_id="test",
        scene_provider=lambda: scene,
    )
    TelemetryService.set_instance(service)
    return service


def events_of(service, event_type):
    return [event["props"] for event in service.pending() if event["type"] == event_type]
