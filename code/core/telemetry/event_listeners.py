"""Turns game events that already exist into research events, through persistent subscriptions."""

# Pickup event -> item name; the props listed are copied when present.
ITEM_EVENTS = {
    "get_key": ("key", ()),
    "resistor_collected": ("resistor", ("value", "area_id")),
    "voltage_source_collected": ("voltage_source", ("value", "area_id")),
    "current_source_collected": ("current_source", ("value", "area_id")),
    "crystal_invisibility_collected": ("crystal_invisibility", ()),
    "cancel_reaggro_after_invisibility": ("anti_reaggro_flask", ()),
}
DIALOGUE_TIMER = "dialogue"
OLD_PAPER_TIMER = "old_paper"


def dialogue_id(entity) -> str:
    name = getattr(entity, "name", None)
    if isinstance(name, str) and name:
        return name
    return type(entity).__name__


def dialogue_line_count(entity) -> int | None:
    # Duck-typed: importing the Dialogue component here would import the UI widgets with it.
    for component in getattr(entity, "components", {}).values():
        lines = getattr(component, "lines", None)
        if isinstance(lines, list):
            return len(lines)
    return None


class TelemetryEventListeners:
    def __init__(self, telemetry):
        self.telemetry = telemetry

    def handlers(self) -> dict:
        handlers = {
            "dialogue_start": self.on_dialogue_start,
            "dialogue_end": self.on_dialogue_end,
            "panel_solved": self.on_panel_solved,
            "open_old_paper": self.on_old_paper_open,
            "close_old_paper": self.on_old_paper_close,
        }
        for event_type in ITEM_EVENTS:
            handlers[event_type] = self.on_item_collected
        return handlers

    def on_dialogue_start(self, event: dict):
        entity = event.get("entity")
        self.telemetry.start_timer(DIALOGUE_TIMER)
        self.telemetry.record("dialogue_start", dialogue_id=dialogue_id(entity), lines=dialogue_line_count(entity))

    def on_dialogue_end(self, event: dict):
        entity = event.get("entity")
        self.telemetry.record(
            "dialogue_end",
            dialogue_id=dialogue_id(entity),
            duration_ms=self.telemetry.stop_timer(DIALOGUE_TIMER),
            lines=dialogue_line_count(entity),
        )

    def on_panel_solved(self, event: dict):
        self.telemetry.record("panel_solved", panel_id=event.get("pannel_id"), panel_file=event.get("panel_file"))

    def on_item_collected(self, event: dict):
        item, copied = ITEM_EVENTS[event["type"]]
        props = {name: event[name] for name in copied if name in event}
        self.telemetry.record("item_collected", item=item, **props)

    def on_old_paper_open(self, event: dict):
        _ = event
        self.telemetry.start_timer(OLD_PAPER_TIMER)
        self.telemetry.record("old_paper_open")

    def on_old_paper_close(self, event: dict):
        _ = event
        self.telemetry.record("old_paper_close", duration_ms=self.telemetry.stop_timer(OLD_PAPER_TIMER))


def _never_raise(handler):
    def safe_handler(event):
        try:
            handler(event)
        except Exception:
            pass

    return safe_handler


def install_event_listeners(event_manager, telemetry) -> None:
    for event_type, handler in TelemetryEventListeners(telemetry).handlers().items():
        event_manager.subscribe_persistent(event_type, _never_raise(handler))
