import json
import os
from pathlib import Path
from typing import Any, List, Type, Dict

from core.settings import CIRCUITOS_DIR

from core.ecs import Entity, Component
from entities.circuit_editor.eletric_components import *
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent


class SerializationManager:

    STORAGE_FOLDER = Path(CIRCUITOS_DIR)
    STORAGE_FILE = STORAGE_FOLDER / "eletric_storage.json"

    # Garante que a pasta exista
    STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    ENTITY_MAP: dict[str, Type[Entity]] = {
        'Resistor': Resistor,
        'Node': Node,
        'VoutageSource': VoutageSource,
        'CurrentSource': CurrentSource,
        'Ground': Ground,
        'Wire': Wire,
    }

    COMPONENT_MAP: dict[str, Type[Component]] = {
        'Position': Position,
        'Sprite': Sprite,
        'LabelComponent': LabelComponent,
        'Connectable': Connectable,
        'Dropped': Dropped,
    }

    @staticmethod
    def load_eletric_storage() -> dict:
        try:
            with open(SerializationManager.STORAGE_FILE, 'r', encoding='utf-8') as f:
                eletric_storage_data = json.load(f)

            return eletric_storage_data

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Arquivo nÃ£o encontrado: {SerializationManager.STORAGE_FILE}"
            )
    def remove_droppable_entities(json_file_path: str):
        """
        Remove entidades de um arquivo JSON que contenham o componente:
        { "type": "Dropped", "can_dropped": true }
        """

        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Arquivo '{json_file_path}' nÃ£o encontrado.")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)

            if not isinstance(entities, list):
                raise ValueError("O JSON raiz deve ser uma lista.")

            def is_droppable(entity: dict) -> bool:
                return any(
                    c.get('type') == 'Dropped' and c.get('can_dropped') is True
                    for c in entity.get('components', [])
                )

            filtered = [e for e in entities if not is_droppable(e)]

            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(filtered, f, indent=4)


           

        except json.JSONDecodeError:
            raise ValueError(f"Falha ao decodificar o arquivo JSON '{json_file_path}'.")
        except Exception as e:
            raise RuntimeError(f"Erro inesperado: {e}")
    @staticmethod
    def save_eletric_storage(data: dict):
        try:
            with open(SerializationManager.STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)


        except Exception:
            pass

    @staticmethod
    def clear_eletric_storage():
        try:
            with open(SerializationManager.STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4)

        except Exception:
            pass

    @staticmethod
    def _resolve_circuit_path(filename: str | Path) -> Path:
        path_obj = Path(filename)
        if path_obj.is_absolute():
            return path_obj
        if len(path_obj.parts) > 0 and path_obj.parts[0].lower() == "circuitos":
            path_obj = Path(*path_obj.parts[1:])
        return SerializationManager.STORAGE_FOLDER / path_obj


    @staticmethod
    def save_entities_to_json(entities: list[Entity], filename: str | Path):
        """
        Salva entities SEMPRE dentro da pasta 'circuitos', a menos que o caminho
        jÃ¡ comece com 'circuitos/' ou seja absoluto.

        Aceita:
            'pannel_1'
            'pannel_1.json'
            'fase_4/pannel_1'
            'fase_4/pannel_1.json'
            'circuitos/pannel_1.json'  (nesse caso nÃ£o duplica a pasta)
        """

        # garante extensÃ£o .json
        filename_str = str(filename)
        my_filename = filename_str if filename_str.endswith(".json") else f"{filename_str}.json"

        final_path = SerializationManager._resolve_circuit_path(my_filename)

        # Se jÃ¡ Ã© absoluto ou jÃ¡ comeÃ§a com 'circuitos', nÃ£o prefixa de novo
        final_path.parent.mkdir(parents=True, exist_ok=True)
        entities_data = [entity.to_dict() for entity in entities]

        final_path.write_text(
            json.dumps(entities_data, indent=4),
            encoding="utf-8"
        )


    @staticmethod
    def load_entities_from_json(filename: str | Path) -> list[Entity]:
        """
        Carrega circuitos SEMPRE da pasta circuitos/, a menos que o caminho
        jÃ¡ venha absoluto ou comeÃ§ando com 'circuitos/'.

        Aceita:
            'pannel_1'
            'pannel_1.json'
            'fase_4/pannel_1'
            'fase_4/pannel_1.json'
            'circuitos/pannel_1.json'
        """

        # forÃ§a extensÃ£o .json
        filename_str = str(filename)
        if not filename_str.endswith(".json"):
            filename_str += ".json"

        filepath = SerializationManager._resolve_circuit_path(filename_str)

        

        # nÃ£o precisa criar pasta pra load, mas nÃ£o machuca:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            entities_data = json.loads(filepath.read_text(encoding="utf-8"))

            reconstructed = [
                SerializationManager.reconstruct_entity(data)
                for data in entities_data
            ]

            return reconstructed

        except FileNotFoundError:
            return []

        except json.JSONDecodeError:
            return []
    @staticmethod
    def update_component_value(netlist_path: str, component_name: str, new_value: str):
        """
        Atualiza o valor de um componente em uma netlist SPICE.
        
        """
        netlist_path = Path(netlist_path)
        with open(netlist_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated_lines = []
        component_found = False

        for line in lines:
            stripped = line.strip()

            # MantÃ©m comentÃ¡rios e linhas vazias
            if stripped.startswith("*") or stripped == "":
                updated_lines.append(line)
                continue

            parts = stripped.split()

            # Se nÃ£o Ã© o componente alvo, mantemos a linha
            if parts[0] != component_name:
                updated_lines.append(line)
                continue

            # Aqui sabemos que Ã© o componente correto â†’ substitui valor
            if len(parts) >= 4:
                parts[-1] = str(new_value)
                updated_line = " ".join(parts) + "\n"
                updated_lines.append(updated_line)
                component_found = True
                continue

            # Caso raro: componente sem valor â†’ erro
            raise ValueError(f"Linha invÃ¡lida para componente '{component_name}': {line}")

        if not component_found:
            raise ValueError(f"Componente '{component_name}' nÃ£o encontrado na netlist.")

        with open(netlist_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
    def update_resistor_labels_in_file(
        self,
        json_file: str | Path,
        label_map: Dict[str, str],
    ) -> None:
        """
        Atualiza o 'value' do LabelComponent de todos os resistores
        com base em um dict {nome_resistor: novo_valor}.

        Ex.: label_map = {"R1": "1k", "R2": "2k2"}
        """
        json_path = (self.base_path / json_file).resolve()

        # Carrega o JSON
        with json_path.open("r", encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)

        # Atualiza os resistores
        for entity in data:
            if entity.get("entity_type") != "Resistor":
                continue

            for comp in entity.get("components", []):
                if comp.get("type") != "LabelComponent":
                    continue

                name = comp.get("name")
                if name in label_map:
                    comp["value"] = label_map[name]

        # Salva de volta
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def remove_resistor_by_name(json_file_path: str, resistor_name: str):
        if not os.path.exists(json_file_path):
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)

            if not isinstance(entities, list):
                return

            def is_target_resistor(entity: dict) -> bool:
                if entity.get("entity_type") != "Resistor":
                    return False

                for comp in entity.get("components", []):
                    if comp.get("type") == "LabelComponent" and comp.get("name") == resistor_name:
                        return True
                return False

            filtered = [e for e in entities if not is_target_resistor(e)]

            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(filtered, f, indent=4, ensure_ascii=False)


        except json.JSONDecodeError:
            pass
        except Exception:
            pass

    @staticmethod
    def reconstruct_entity(data: dict) -> Entity:
        entity_type_name = data['entity_type']
        EntityClass = SerializationManager.ENTITY_MAP.get(entity_type_name)

        if not EntityClass:
            raise ValueError(f"Tipo desconhecido: {entity_type_name}")

        new_entity = EntityClass.__new__(EntityClass)
        Entity.__init__(new_entity)

        for comp_data in data['components']:
            comp_type_name = comp_data['type']
            ComponentClass = SerializationManager.COMPONENT_MAP.get(comp_type_name)

            if not ComponentClass:
                raise ValueError(f"Componente desconhecido: {comp_type_name}")

            component_instance = ComponentClass.from_dict(comp_data)
            new_entity.add(component_instance)

        return new_entity
