from pathlib import Path

# The pygbag filesystem lives in memory and is lost on page reload, so the
# browser build mirrors its writable JSON data into localStorage.
KEY_PREFIX = "alexandria:"
DATA_PATTERN = "*.json"


class WebStorageSync:
    def __init__(self, root: Path, data_dirs: list[Path], storage):
        self.root = Path(root)
        self.data_dirs = [Path(data_dir) for data_dir in data_dirs]
        self.storage = storage
        self._known_mtimes: dict[Path, int] = {}

    def restore(self) -> None:
        for index in range(self.storage.length):
            key = self.storage.key(index)
            if not key.startswith(KEY_PREFIX):
                continue
            path = self.root / key[len(KEY_PREFIX):]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.storage.getItem(key), encoding="utf-8")
        self._known_mtimes = self._scan_mtimes()

    def persist_changes(self) -> None:
        current = self._scan_mtimes()
        for path, mtime in current.items():
            if self._known_mtimes.get(path) != mtime:
                self.storage.setItem(self._key(path), path.read_text(encoding="utf-8"))
        for path in self._known_mtimes.keys() - current.keys():
            self.storage.removeItem(self._key(path))
        self._known_mtimes = current

    def _scan_mtimes(self) -> dict[Path, int]:
        return {
            path: path.stat().st_mtime_ns
            for data_dir in self.data_dirs
            for path in data_dir.rglob(DATA_PATTERN)
        }

    def _key(self, path: Path) -> str:
        return KEY_PREFIX + path.relative_to(self.root).as_posix()
