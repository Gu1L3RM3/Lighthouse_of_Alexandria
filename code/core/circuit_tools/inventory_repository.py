from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from core.circuit_tools.circuit_domain import CircuitError
from core.circuit_tools.legacy_circuit_aliases import (
    LEGACY_VOLTAGE_SOURCE_ENTITY,
    VOLTAGE_SOURCE_ENTITY,
)
from core.settings import CIRCUITOS_DIR


class InventoryError(CircuitError):
    pass


class InventoryRepository:
    LEGACY_VOLTAGE_SOURCE = LEGACY_VOLTAGE_SOURCE_ENTITY
    VOLTAGE_SOURCE = VOLTAGE_SOURCE_ENTITY

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

        normalized = {str(kind): dict(values) for kind, values in payload.items()}
        legacy = normalized.pop(self.LEGACY_VOLTAGE_SOURCE, {})
        voltage_sources = normalized.setdefault(self.VOLTAGE_SOURCE, {}) if legacy else normalized.get(self.VOLTAGE_SOURCE)
        if voltage_sources is not None:
            for value, count in legacy.items():
                voltage_sources[str(value)] = int(voltage_sources.get(str(value), 0)) + int(count)
        return normalized

    def save(self, inventory: dict[str, dict[str, int]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"
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
