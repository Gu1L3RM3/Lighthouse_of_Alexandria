from __future__ import annotations

import json
from pathlib import Path

from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.settings import CIRCUITOS_DIR


INVENTORY_FILE = "eletric_storage.json"
KNOWN_DUPLICATE_FILES = {
    Path("generic_levels_5/fase_5/pannel2.json"),
    Path("generic_levels_5/fase_5/pannel2_solution.json"),
}


def _repair_known_duplicate(payload: list[dict], relative_path: Path) -> None:
    if relative_path not in KNOWN_DUPLICATE_FILES:
        return

    seen_r2 = False
    for entity in payload:
        for component in entity.get("components", []):
            if component.get("type") != "LabelComponent" or component.get("name") != "R2":
                continue
            if seen_r2:
                component["name"] = "R6"
                return
            seen_r2 = True


def migrate_circuit_directory(root: Path = CIRCUITOS_DIR) -> list[Path]:
    repository = CircuitJsonRepository()
    migrated: list[Path] = []
    for path in sorted(root.rglob("*.json")):
        if path.name == INVENTORY_FILE:
            continue
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            _repair_known_duplicate(payload, path.relative_to(root))
        document = repository.decode(payload)
        repository.save(path, document)
        migrated.append(path)
    return migrated


if __name__ == "__main__":
    for migrated_path in migrate_circuit_directory():
        print(migrated_path)
