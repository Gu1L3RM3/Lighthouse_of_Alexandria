from core.telemetry.service import TelemetryService


class PanelStatusReporter:
    """Records a validator's panel status only when it changes (validators re-check every few frames)."""

    def __init__(self, level_path: str, tolerance_percent: float | None = None, telemetry_provider=TelemetryService.get):
        self.level_path = str(level_path).replace("\\", "/")
        self.tolerance_percent = tolerance_percent
        self.telemetry_provider = telemetry_provider
        self._last_status: dict[int, str] = {}

    def report(self, panel_id, status: str, *, measured=None, expected=None, solution_type=None) -> None:
        try:
            key = int(panel_id)
        except (TypeError, ValueError):
            return
        if self._last_status.get(key) == status:
            return
        self._last_status[key] = status
        self.telemetry_provider().record(
            "panel_status",
            panel_id=key,
            panel_file=f"{self.level_path}/pannel{key}",
            status=status,
            measured=measured,
            expected=expected,
            tolerance_percent=self.tolerance_percent,
            solution_type=solution_type,
        )
