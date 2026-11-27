"""Derives scene, editor, idle, visibility and input-source events from per-frame observations."""

IDLE_THRESHOLD_MS = 60_000
# A frame gap longer than this means the browser paused the game (e.g. a background tab):
# only this much of it counts as active time.
MAX_FRAME_GAP_MS = 5_000
HIDDEN_STATE = "hidden"
VISIBLE_STATE = "visible"

SCENE_CATEGORY_BY_NAME = {
    "main_menu": "menu",
    "credits": "menu",
    "help": "menu",
    "home_scene": "intro",
    "home_after": "intro",
    "level_1": "story",
    "level_2": "story",
    "death_transition": "cutscene",
    "circuit_editor_boot": "editor",
}
SCENE_CATEGORY_BY_PREFIX = (("exp_", "explanation"), ("ending_", "cutscene"))
DEFAULT_SCENE_CATEGORY = "puzzle"


def scene_category(scene_name: str | None) -> str:
    name = scene_name or ""
    if name in SCENE_CATEGORY_BY_NAME:
        return SCENE_CATEGORY_BY_NAME[name]
    for prefix, category in SCENE_CATEGORY_BY_PREFIX:
        if name.startswith(prefix):
            return category
    return DEFAULT_SCENE_CATEGORY


def editor_info(scene) -> dict | None:
    """The circuit editor is not a registered scene; it describes itself instead."""
    describe = getattr(scene, "telemetry_editor_info", None)
    if not callable(describe):
        return None
    try:
        return describe()
    except Exception:
        return None


class SessionTracker:
    def __init__(
        self,
        telemetry,
        idle_threshold_ms: int = IDLE_THRESHOLD_MS,
        max_frame_gap_ms: int = MAX_FRAME_GAP_MS,
        categorize=scene_category,
    ):
        self.telemetry = telemetry
        self.idle_threshold_ms = idle_threshold_ms
        self.max_frame_gap_ms = max_frame_gap_ms
        self.categorize = categorize
        now = telemetry.elapsed_ms()
        self._last_tick = now
        self._last_input = now
        self._idle_since: int | None = None
        self._visibility = VISIBLE_STATE
        self._input_source: str | None = None
        self._session_active_ms = 0
        self._scene_name: str | None = None
        self._scene_started = now
        self._scene_active_ms = 0
        self._editor = None
        self._editor_started = now
        self._editor_active_ms = 0

    def observe_frame(self, scene_name: str | None, scene, had_input: bool, input_source: str | None) -> None:
        try:
            now = self._advance()
            self._observe_input(now, had_input)
            self._observe_input_source(input_source)
            self._observe_editor(now, scene)
            self._observe_scene(now, scene_name)
        except Exception:
            pass

    def observe_visibility(self, state: str | None) -> None:
        if state is None or state == self._visibility:
            return
        self._advance()
        self._visibility = state
        self.telemetry.record("visibility", state=state)

    def finish(self) -> None:
        now = self._advance()
        if self._idle_since is not None:
            self._end_idle(now)
        self._close_editor(now)
        self._exit_scene(now)
        self.telemetry.record("session_end", duration_ms=now, active_ms=self._session_active_ms)

    def _advance(self) -> int:
        now = self.telemetry.elapsed_ms()
        gap = min(max(0, now - self._last_tick), self.max_frame_gap_ms)
        self._last_tick = now
        if self._idle_since is None and self._visibility != HIDDEN_STATE:
            self._scene_active_ms += gap
            self._session_active_ms += gap
            self._editor_active_ms += gap
        return now

    def _observe_input(self, now: int, had_input: bool) -> None:
        if had_input:
            self._last_input = now
            if self._idle_since is not None:
                self._end_idle(now)
            return
        if self._idle_since is None and now - self._last_input >= self.idle_threshold_ms:
            self._idle_since = now
            self.telemetry.record("idle_start")

    def _end_idle(self, now: int) -> None:
        self.telemetry.record("idle_end", idle_ms=now - self._idle_since)
        self._idle_since = None

    def _observe_input_source(self, source: str | None) -> None:
        if source is None or source == self._input_source:
            return
        if self._input_source is not None:
            self.telemetry.record("input_source_change", source=source)
        self._input_source = source

    def _observe_editor(self, now: int, scene) -> None:
        if scene is self._editor:
            return
        self._close_editor(now)
        info = editor_info(scene)
        if info is None:
            return
        self._editor = scene
        self._editor_started = now
        self._editor_active_ms = 0
        self.telemetry.record("editor_open", panel_file=info.get("panel_file"), kind=info.get("kind"))

    def _close_editor(self, now: int) -> None:
        if self._editor is None:
            return
        info = editor_info(self._editor) or {}
        self._editor = None
        self.telemetry.record(
            "editor_close",
            panel_file=info.get("panel_file"),
            kind=info.get("kind"),
            duration_ms=now - self._editor_started,
            active_ms=self._editor_active_ms,
            saved=bool(info.get("saved")),
        )

    def _observe_scene(self, now: int, scene_name: str | None) -> None:
        if scene_name == self._scene_name:
            return
        self._exit_scene(now)
        self._scene_name = scene_name
        self._scene_started = now
        self._scene_active_ms = 0
        if scene_name is not None:
            self.telemetry.record("scene_enter", scene=scene_name, category=self.categorize(scene_name))

    def _exit_scene(self, now: int) -> None:
        if self._scene_name is None:
            return
        self.telemetry.record(
            "scene_exit",
            scene=self._scene_name,
            category=self.categorize(self._scene_name),
            duration_ms=now - self._scene_started,
            active_ms=self._scene_active_ms,
        )
        self._scene_name = None
