class NullTransport:
    """Default transport: desktop, itch.io and tests record nothing."""

    enabled = False

    def send(self, payload: str) -> None:
        _ = payload


class WebBridgeTransport:
    """Hands batches to the bridge a hosting page defines as `window.alexTelemetry`."""

    enabled = True

    def __init__(self, window):
        self.window = window

    def send(self, payload: str) -> None:
        self.window.alexTelemetry.push(payload)
