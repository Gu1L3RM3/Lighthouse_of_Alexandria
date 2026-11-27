import json
import math
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Callable

from core.telemetry.transports import NullTransport

SCHEMA_VERSION = 1
MAX_BATCH_EVENTS = 200
MAX_QUEUED_EVENTS = 2000
DROPPED_EVENT_TYPE = "telemetry_dropped"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value):
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


class TelemetryService:
    """Queues research events and hands them to a transport in bounded JSON batches.

    It must never break the game: every public method swallows its own errors.
    """

    _instance = None

    def __init__(
        self,
        transport=None,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = _utc_now,
        session_id: str | None = None,
        scene_provider: Callable[[], str | None] | None = None,
        max_batch: int = MAX_BATCH_EVENTS,
        max_queue: int = MAX_QUEUED_EVENTS,
    ):
        self.transport = transport or NullTransport()
        self.clock = clock
        self.wall_clock = wall_clock
        self.session_id = session_id or uuid.uuid4().hex
        self.scene_provider = scene_provider
        self.max_batch = max_batch
        self.max_queue = max_queue
        self._started_at = clock()
        self._seq = 0
        self._queue: deque = deque()
        self._dropped = 0
        self._timers: dict[str, float] = {}

    @classmethod
    def get(cls) -> "TelemetryService":
        if cls._instance is None:
            cls._instance = TelemetryService()
        return cls._instance

    @classmethod
    def set_instance(cls, service: "TelemetryService") -> None:
        cls._instance = service

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    @property
    def enabled(self) -> bool:
        return bool(getattr(self.transport, "enabled", False))

    def elapsed_ms(self) -> int:
        return int(round((self.clock() - self._started_at) * 1000))

    def record(self, event_type: str, **props) -> None:
        if not self.enabled:
            return
        try:
            self._append(self._build_event(event_type, props))
        except Exception:
            pass

    def start_timer(self, key: str) -> None:
        self._timers[key] = self.clock()

    def stop_timer(self, key: str) -> int | None:
        started = self._timers.pop(key, None)
        if started is None:
            return None
        return int(round((self.clock() - started) * 1000))

    def pending(self) -> list[dict]:
        return list(self._queue)

    def flush(self) -> bool:
        """Sends one batch; on a bridge error keeps it for the next flush."""
        if not self.enabled:
            return True
        try:
            if self._dropped:
                count, self._dropped = self._dropped, 0
                self._append(self._build_event(DROPPED_EVENT_TYPE, {"count": count}))
            if not self._queue:
                return True
            batch = [self._queue[index] for index in range(min(self.max_batch, len(self._queue)))]
            self.transport.send(json.dumps(batch, separators=(",", ":"), allow_nan=False))
        except Exception:
            return False
        for _ in batch:
            self._queue.popleft()
        return True

    def flush_all(self) -> None:
        while self._queue or self._dropped:
            if not self.flush():
                return

    def _build_event(self, event_type: str, props: dict) -> dict:
        self._seq += 1
        timestamp = self.wall_clock().astimezone(timezone.utc)
        return {
            "v": SCHEMA_VERSION,
            "seq": self._seq,
            "session_id": self.session_id,
            "t_ms": self.elapsed_ms(),
            "ts": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "scene": self._current_scene(),
            "type": event_type,
            "props": _json_safe(props),
        }

    def _current_scene(self) -> str | None:
        if self.scene_provider is None:
            return None
        try:
            scene = self.scene_provider()
        except Exception:
            return None
        return None if scene is None else str(scene)

    def _append(self, event: dict) -> None:
        if len(self._queue) >= self.max_queue:
            self._queue.popleft()
            self._dropped += 1
        self._queue.append(event)
