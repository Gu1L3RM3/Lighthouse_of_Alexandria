"""Opt-in research telemetry: records nothing unless the hosting page defines `window.alexTelemetry`.

The contract with the hosting page is documented in docs/agents/telemetry.md.
"""

from core.telemetry.service import TelemetryService
from core.telemetry.transports import NullTransport, WebBridgeTransport

__all__ = ["NullTransport", "TelemetryService", "WebBridgeTransport"]
