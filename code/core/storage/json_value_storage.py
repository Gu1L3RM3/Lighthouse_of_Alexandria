from __future__ import annotations

import json
from typing import Any


class BrowserJsonValueStorage:
    _fallback_memory: dict[str, str] = {}

    def __init__(self, storage_key: str, storage_adapter: object | None = None):
        self.storage_key = storage_key
        self.storage_adapter = storage_adapter or self._resolve_storage_adapter()

    def exists(self) -> bool:
        return self._read_raw() is not None

    def load(self) -> Any | None:
        raw = self._read_raw()
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def save(self, payload: Any) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2)
        self._write_raw(raw)

    def clear(self) -> None:
        adapter = self.storage_adapter
        if adapter is None:
            self._fallback_memory.pop(self.storage_key, None)
            return
        try:
            adapter.removeItem(self.storage_key)
        except Exception:
            self._fallback_memory.pop(self.storage_key, None)

    def _read_raw(self) -> str | None:
        adapter = self.storage_adapter
        if adapter is None:
            return self._fallback_memory.get(self.storage_key)
        try:
            return adapter.getItem(self.storage_key)
        except Exception:
            return self._fallback_memory.get(self.storage_key)

    def _write_raw(self, raw: str) -> None:
        adapter = self.storage_adapter
        if adapter is None:
            self._fallback_memory[self.storage_key] = raw
            return
        try:
            adapter.setItem(self.storage_key, raw)
        except Exception:
            self._fallback_memory[self.storage_key] = raw

    def _resolve_storage_adapter(self):
        try:
            from platform import window  # type: ignore

            return window.localStorage
        except Exception:
            return None


class InMemoryJsonValueStorage:
    def __init__(self, initial_data: Any | None = None):
        self._data = initial_data

    def exists(self) -> bool:
        return self._data is not None

    def load(self) -> Any | None:
        return self._data

    def save(self, payload: Any) -> None:
        self._data = payload

    def clear(self) -> None:
        self._data = None

