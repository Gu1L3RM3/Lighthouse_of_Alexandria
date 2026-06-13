from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol


class JsonDocumentStorage(Protocol):
    def exists(self) -> bool:
        ...

    def load(self) -> dict[str, Any] | None:
        ...

    def save(self, payload: dict[str, Any]) -> None:
        ...

    def clear(self) -> None:
        ...


class FileJsonDocumentStorage:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        return self.file_path.exists()

    def load(self) -> dict[str, Any] | None:
        if not self.exists():
            return None
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def save(self, payload: dict[str, Any]) -> None:
        tmp_file = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        try:
            tmp_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_file.replace(self.file_path)
        except Exception:
            pass

    def clear(self) -> None:
        try:
            self.file_path.unlink(missing_ok=True)
        except Exception:
            pass


class BrowserJsonDocumentStorage:
    _fallback_memory: dict[str, str] = {}

    def __init__(self, storage_key: str, storage_adapter: object | None = None):
        self.storage_key = storage_key
        self.storage_adapter = storage_adapter or self._resolve_storage_adapter()

    def exists(self) -> bool:
        return self._read_raw() is not None

    def load(self) -> dict[str, Any] | None:
        raw = self._read_raw()
        if raw is None:
            return None
        try:
            data = json.loads(raw)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def save(self, payload: dict[str, Any]) -> None:
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


class InMemoryJsonDocumentStorage:
    def __init__(self, initial_data: dict[str, Any] | None = None):
        self._data = dict(initial_data) if initial_data is not None else None

    def exists(self) -> bool:
        return self._data is not None

    def load(self) -> dict[str, Any] | None:
        if self._data is None:
            return None
        return dict(self._data)

    def save(self, payload: dict[str, Any]) -> None:
        self._data = dict(payload)

    def clear(self) -> None:
        self._data = None

