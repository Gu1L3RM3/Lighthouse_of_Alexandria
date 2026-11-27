class SlideTracker:
    """Times each explanation slide (one dialogue line with its image) the player looks at."""

    def __init__(self, telemetry):
        self.telemetry = telemetry
        self._current: tuple[str, int] | None = None
        self._started_ms = 0

    def observe(self, dialogue_id: str | None, index: int | None) -> None:
        slide = None if dialogue_id is None or index is None else (dialogue_id, int(index))
        if slide == self._current:
            return
        now = self.telemetry.elapsed_ms()
        if self._current is not None:
            self.telemetry.record(
                "explanation_slide",
                dialogue_id=self._current[0],
                index=self._current[1],
                duration_ms=now - self._started_ms,
            )
        self._current = slide
        self._started_ms = now
