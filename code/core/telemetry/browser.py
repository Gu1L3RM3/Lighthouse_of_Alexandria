"""Reads what the hosting page offers through pygbag's `platform.window`; any JS error means "absent"."""

from core.telemetry.transports import NullTransport, WebBridgeTransport
from core.web_storage_sync import KEY_PREFIX

WEB_PLATFORM = "emscripten"


def _read(window, *names):
    value = window
    try:
        for name in names:
            value = getattr(value, name, None)
            if value is None:
                return None
    except Exception:
        return None
    return value


def create_transport(platform_name: str, window):
    if platform_name != WEB_PLATFORM or window is None:
        return NullTransport()
    if _read(window, "alexTelemetry") is None:
        return NullTransport()
    return WebBridgeTransport(window)


def read_storage_prefix(window) -> str:
    prefix = _read(window, "ALEX_STORAGE_PREFIX")
    if isinstance(prefix, str) and prefix:
        return prefix
    return KEY_PREFIX


def read_visibility_state(window) -> str | None:
    state = _read(window, "document", "visibilityState")
    return str(state) if state is not None else None


def read_viewport_size(window) -> tuple[int, int] | None:
    width = _read(window, "innerWidth")
    height = _read(window, "innerHeight")
    try:
        return int(width), int(height)
    except (TypeError, ValueError):
        return None
