from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from core.circuit_tools.circuit_domain import CircuitError
from core.circuit_tools.legacy_circuit_aliases import (
    normalize_inventory_component_type,
)
from core.settings import CIRCUITOS_DIR


class InventoryError(CircuitError):
    pass


class InventoryRepository:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else Path(CIRCUITOS_DIR) / "eletric_storage.json"

    def load(self) -> dict[str, dict[str, int]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as error:
            raise InventoryError(f"Inventory not found: {self.path}") from error
        except json.JSONDecodeError as error:
            raise InventoryError(f"Invalid inventory JSON: {self.path}") from error
        if not isinstance(payload, dict):
            raise InventoryError("Inventory must be a JSON object")

        normalized: dict[str, dict[str, int]] = {}
        for raw_kind, raw_values in payload.items():
            try:
                kind = normalize_inventory_component_type(str(raw_kind))
            except ValueError as error:
                raise InventoryError(str(error)) from error
            if not isinstance(raw_values, dict):
                raise InventoryError(f"Inventory values for {kind} must be a JSON object")
            values = normalized.setdefault(kind, {})
            for raw_value, raw_count in raw_values.items():
                value = str(raw_value)
                values[value] = values.get(value, 0) + int(raw_count)
        return normalized

    def save(self, inventory: dict[str, dict[str, int]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized = self._normalize_inventory(inventory)
        content = json.dumps(normalized, indent=2, ensure_ascii=False) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.replace(self.path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def clear(self) -> None:
        self.save({})

    def _normalize_inventory(self, inventory: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
        try:
            payload = json.loads(json.dumps(inventory))
        except (TypeError, ValueError) as error:
            raise InventoryError("Inventory must contain JSON-compatible values") from error
        if not isinstance(payload, dict):
            raise InventoryError("Inventory must be a JSON object")

        normalized: dict[str, dict[str, int]] = {}
        for raw_kind, raw_values in payload.items():
            try:
                kind = normalize_inventory_component_type(str(raw_kind))
            except ValueError as error:
                raise InventoryError(str(error)) from error
            if not isinstance(raw_values, dict):
                raise InventoryError(f"Inventory values for {kind} must be a JSON object")
            values = normalized.setdefault(kind, {})
            for raw_value, raw_count in raw_values.items():
                value = str(raw_value)
                values[value] = values.get(value, 0) + int(raw_count)
        return normalized
