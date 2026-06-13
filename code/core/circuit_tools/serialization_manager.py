import json
from pathlib import Path
from typing import Any, Dict, List, Type

from core.components.connectable import Connectable
from core.components.dropped import Dropped
from core.components.label_component import LabelComponent
from core.components.position import Position
from core.components.sprite import Sprite
from core.ecs import Component, Entity
from core.settings import CIRCUITOS_DIR
from core.storage.json_value_storage import BrowserJsonValueStorage
from entities.circuit_editor.eletric_components import CurrentSource, Ground, Node, Resistor, VoutageSource, Wire


class SerializationManager:
    STORAGE_KEY = "alexandria.circuit.eletric_storage"
    CIRCUIT_KEY_PREFIX = "alexandria.circuit.file"
    NETLIST_KEY_PREFIX = "alexandria.netlist.file"
    _storage_builder = staticmethod(lambda key: BrowserJsonValueStorage(key))

    ENTITY_MAP: dict[str, Type[Entity]] = {
        "Resistor": Resistor,
        "Node": Node,
        "VoutageSource": VoutageSource,
        "CurrentSource": CurrentSource,
        "Ground": Ground,
        "Wire": Wire,
    }

    COMPONENT_MAP: dict[str, Type[Component]] = {
        "Position": Position,
        "Sprite": Sprite,
        "LabelComponent": LabelComponent,
        "Connectable": Connectable,
        "Dropped": Dropped,
    }

    @staticmethod
    def load_eletric_storage() -> dict:
        data = SerializationManager._storage_builder(SerializationManager.STORAGE_KEY).load()
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def save_eletric_storage(data: dict):
        SerializationManager._storage_builder(SerializationManager.STORAGE_KEY).save(data)

    @staticmethod
    def clear_eletric_storage():
        SerializationManager._storage_builder(SerializationManager.STORAGE_KEY).save({})

    @staticmethod
    def _normalize_filename(filename: str | Path) -> str:
        path_obj = Path(filename)
        if len(path_obj.parts) > 0 and path_obj.parts[0].lower() == "circuitos":
            path_obj = Path(*path_obj.parts[1:])
        normalized = path_obj.as_posix()
        if not normalized.endswith(".json"):
            normalized += ".json"
        return normalized

    @staticmethod
    def _circuit_storage_key(filename: str | Path) -> str:
        return f"{SerializationManager.CIRCUIT_KEY_PREFIX}:{SerializationManager._normalize_filename(filename)}"

    @staticmethod
    def _bundled_circuit_path(filename: str | Path) -> Path:
        return Path(CIRCUITOS_DIR) / SerializationManager._normalize_filename(filename)

    @staticmethod
    def _netlist_storage_key(filename: str | Path) -> str:
        return f"{SerializationManager.NETLIST_KEY_PREFIX}:{Path(filename).as_posix()}"

    @staticmethod
    def save_entities_to_json(entities: list[Entity], filename: str | Path):
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(filename)
        )
        storage.save([entity.to_dict() for entity in entities])

    @staticmethod
    def save_entities_data(data: list[dict], filename: str | Path):
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(filename)
        )
        storage.save(data)

    @staticmethod
    def load_entities_from_json(filename: str | Path) -> list[Entity]:
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(filename)
        )
        entities_data = storage.load()
        if not isinstance(entities_data, list):
            bundled_path = SerializationManager._bundled_circuit_path(filename)
            try:
                entities_data = json.loads(bundled_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        if not isinstance(entities_data, list):
            return []
        try:
            return [SerializationManager.reconstruct_entity(data) for data in entities_data]
        except Exception:
            return []

    @staticmethod
    def load_entities_data(filename: str | Path) -> list[dict]:
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(filename)
        )
        entities_data = storage.load()
        if isinstance(entities_data, list):
            return entities_data
        bundled_path = SerializationManager._bundled_circuit_path(filename)
        try:
            entities_data = json.loads(bundled_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return entities_data if isinstance(entities_data, list) else []

    @staticmethod
    def remove_droppable_entities(json_file_path: str):
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(json_file_path)
        )
        entities = storage.load()
        if not isinstance(entities, list):
            raise ValueError("O JSON raiz deve ser uma lista.")

        filtered = [
            entity for entity in entities
            if not any(
                component.get("type") == "Dropped" and component.get("can_dropped") is True
                for component in entity.get("components", [])
            )
        ]
        storage.save(filtered)

    @staticmethod
    def update_component_value(netlist_path: str, component_name: str, new_value: str):
        storage = SerializationManager._storage_builder(
            SerializationManager._netlist_storage_key(netlist_path)
        )
        current_text = storage.load()
        if not isinstance(current_text, str):
            try:
                current_text = Path(netlist_path).read_text(encoding="utf-8")
            except Exception:
                return None

        lines = current_text.splitlines()
        updated_lines = []
        component_found = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("*") or stripped == "":
                updated_lines.append(line)
                continue

            parts = stripped.split()
            if not parts or parts[0] != component_name:
                updated_lines.append(line)
                continue

            if len(parts) >= 4:
                parts[-1] = str(new_value)
                updated_lines.append(" ".join(parts))
                component_found = True
                continue

            raise ValueError(f"Linha invalida para componente '{component_name}': {line}")

        if not component_found:
            raise ValueError(f"Componente '{component_name}' nao encontrado na netlist.")

        storage.save("\n".join(updated_lines) + "\n")
        return None

    @staticmethod
    def load_netlist_text(netlist_path: str | Path) -> str | None:
        storage = SerializationManager._storage_builder(
            SerializationManager._netlist_storage_key(netlist_path)
        )
        current_text = storage.load()
        if isinstance(current_text, str):
            return current_text
        try:
            return Path(netlist_path).read_text(encoding="utf-8")
        except Exception:
            return None

    @staticmethod
    def save_netlist_text(netlist_path: str | Path, netlist_text: str) -> None:
        storage = SerializationManager._storage_builder(
            SerializationManager._netlist_storage_key(netlist_path)
        )
        storage.save(netlist_text)

    @staticmethod
    def iter_netlist_lines(netlist_path: str | Path) -> list[str]:
        netlist_text = SerializationManager.load_netlist_text(netlist_path)
        if netlist_text is None:
            return []
        return netlist_text.splitlines()

    def update_resistor_labels_in_file(
        self,
        json_file: str | Path,
        label_map: Dict[str, str],
    ) -> None:
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(json_file)
        )
        data: Any = storage.load()
        if not isinstance(data, list):
            return

        for entity in data:
            if entity.get("entity_type") != "Resistor":
                continue
            for component in entity.get("components", []):
                if component.get("type") != "LabelComponent":
                    continue
                name = component.get("name")
                if name in label_map:
                    component["value"] = label_map[name]

        storage.save(data)

    @staticmethod
    def remove_resistor_by_name(json_file_path: str, resistor_name: str):
        storage = SerializationManager._storage_builder(
            SerializationManager._circuit_storage_key(json_file_path)
        )
        entities = storage.load()
        if not isinstance(entities, list):
            return

        def is_target_resistor(entity: dict) -> bool:
            if entity.get("entity_type") != "Resistor":
                return False
            for component in entity.get("components", []):
                if component.get("type") == "LabelComponent" and component.get("name") == resistor_name:
                    return True
            return False

        storage.save([entity for entity in entities if not is_target_resistor(entity)])

    @staticmethod
    def reconstruct_entity(data: dict) -> Entity:
        entity_type_name = data["entity_type"]
        entity_class = SerializationManager.ENTITY_MAP.get(entity_type_name)
        if not entity_class:
            raise ValueError(f"Tipo desconhecido: {entity_type_name}")

        new_entity = entity_class.__new__(entity_class)
        Entity.__init__(new_entity)

        for comp_data in data["components"]:
            comp_type_name = comp_data["type"]
            component_class = SerializationManager.COMPONENT_MAP.get(comp_type_name)
            if not component_class:
                raise ValueError(f"Componente desconhecido: {comp_type_name}")
            new_entity.add(component_class.from_dict(comp_data))

        return new_entity
