from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from core.circuit_tools.circuit_domain import (
    CircuitDocument,
    CircuitElement,
    CircuitValidationError,
    ElementKind,
)


_LEGACY_KIND_MAP = {
    "Resistor": ElementKind.RESISTOR,
    "VoutageSource": ElementKind.VOLTAGE_SOURCE,
    "VoltageSource": ElementKind.VOLTAGE_SOURCE,
    "CurrentSource": ElementKind.CURRENT_SOURCE,
    "Wire": ElementKind.WIRE,
    "Node": ElementKind.NODE,
    "Ground": ElementKind.GROUND,
}


class CircuitNotFoundError(CircuitValidationError):
    pass


class CircuitFormatError(CircuitValidationError):
    pass


class CircuitJsonRepository:
    def load(self, path: str | Path) -> CircuitDocument:
        circuit_path = Path(path)
        try:
            payload = json.loads(circuit_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            raise CircuitNotFoundError(f"Circuit not found: {circuit_path}") from exc
        except json.JSONDecodeError as exc:
            raise CircuitFormatError(f"Invalid circuit JSON: {circuit_path}") from exc

        try:
            return self.decode(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise CircuitFormatError(f"Invalid circuit data: {circuit_path}") from exc

    def decode(self, payload: Any) -> CircuitDocument:
        if isinstance(payload, list):
            return self._decode_v1(payload)
        if isinstance(payload, dict) and payload.get("schema_version") == 2:
            return self._decode_v2(payload)
        raise CircuitFormatError("Unsupported circuit schema")

    def save(self, path: str | Path, document: CircuitDocument) -> None:
        circuit_path = Path(path)
        circuit_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.to_payload(document), indent=2, ensure_ascii=False) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{circuit_path.name}.", suffix=".tmp", dir=circuit_path.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.replace(circuit_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def to_payload(self, document: CircuitDocument) -> dict[str, Any]:
        elements: list[dict[str, Any]] = []
        for element in document.elements:
            item: dict[str, Any] = {
                "kind": element.kind.value,
                "x": element.x,
                "y": element.y,
                "rotation": element.rotation,
                "editable": element.editable,
            }
            if element.kind.is_electrical:
                item["name"] = element.name
                item["value"] = element.value
            elements.append(item)
        return {"schema_version": 2, "elements": elements}

    def _decode_v2(self, payload: dict[str, Any]) -> CircuitDocument:
        raw_elements = payload.get("elements")
        if not isinstance(raw_elements, list):
            raise CircuitFormatError("Circuit elements must be a list")
        return CircuitDocument(
            elements=tuple(
                CircuitElement(
                    kind=ElementKind(item["kind"]),
                    x=item["x"],
                    y=item["y"],
                    rotation=item.get("rotation", 0),
                    editable=bool(item.get("editable", True)),
                    name=item.get("name"),
                    value=item.get("value"),
                )
                for item in raw_elements
            )
        )

    def _decode_v1(self, payload: list[dict[str, Any]]) -> CircuitDocument:
        elements: list[CircuitElement] = []
        for entity in payload:
            kind = _LEGACY_KIND_MAP[entity["entity_type"]]
            components = {item["type"]: item for item in entity.get("components", [])}
            position = components["Position"]
            sprite = components.get("Sprite", {})
            dropped = components.get("Dropped", {})
            label = components.get("LabelComponent", {})
            elements.append(
                CircuitElement(
                    kind=kind,
                    x=position["x"],
                    y=position["y"],
                    rotation=sprite.get("angle", 0),
                    editable=bool(dropped.get("can_dropped", True)),
                    name=label.get("name") if kind.is_electrical else None,
                    value=label.get("value") if kind.is_electrical else None,
                )
            )
        return CircuitDocument(tuple(elements))
