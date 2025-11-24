import json
import os
from typing import Type
from core.ecs import Entity, Component
from entities.circuit_editor.eletric_components import *
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent


class SerializationManager:

    STORAGE_FOLDER = "circuitos"
    STORAGE_FILE = os.path.join(STORAGE_FOLDER, "eletric_storage.json")

    # Garante que a pasta exista
    if not os.path.exists(STORAGE_FOLDER):
        os.makedirs(STORAGE_FOLDER)

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
            with open(SerializationManager.STORAGE_FILE, 'r') as f:
                eletric_storage_data = json.load(f)

            print(f"Eletric Storage carregado de {SerializationManager.STORAGE_FILE}")
            return eletric_storage_data

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Arquivo não encontrado: {SerializationManager.STORAGE_FILE}"
            )
    def remove_droppable_entities(json_file_path: str):
        """
        Remove entidades de um arquivo JSON que contenham o componente:
        { "type": "Dropped", "can_dropped": true }
        """

        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Arquivo '{json_file_path}' não encontrado.")

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
            with open(SerializationManager.STORAGE_FILE, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"Estoque elétrico salvo em {SerializationManager.STORAGE_FILE}")

        except Exception as e:
            print(f"Erro ao salvar: {e}")

    @staticmethod
    def clear_eletric_storage():
        try:
            with open(SerializationManager.STORAGE_FILE, 'w') as f:
                json.dump({}, f, indent=4)

            print("Eletric Storage limpo com sucesso.")
        except Exception as e:
            print(f"Erro ao limpar: {e}")

    @staticmethod
    def save_entities_to_json(entities: list[Entity], filename: str):
        """
        Salva entities SEMPRE dentro da pasta circuitos.
        filename deve ser apenas o nome, ex: 'meu_circuito.json'
        """
        
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join( filename)

        entities_data = [entity.to_dict() for entity in entities]

        with open(filepath, 'w') as f:
            json.dump(entities_data, f, indent=4)

        print(f"Circuito salvo em {filepath}")

    @staticmethod
    def load_entities_from_json(filename: str) -> list[Entity]:
        """
        Carrega circuitos SEMPRE da pasta circuitos/.
        filename deve ser apenas o nome, ex: 'meu_circuito.json'
        """
        if not filename.endswith(".json"):
            filename += ".json"

        filepath = os.path.join(SerializationManager.STORAGE_FOLDER, filename)

        try:
            with open(filepath, 'r') as f:
                entities_data = json.load(f)

            reconstructed = [
                SerializationManager.reconstruct_entity(data)
                for data in entities_data
            ]

            print(f"Circuito carregado de {filepath}")
            return reconstructed

        except FileNotFoundError:
            print(f"Circuito não encontrado: {filepath}")
            return []
    @staticmethod
    def update_component_value(netlist_path: str, component_name: str, new_value: str):
        """
        Atualiza o valor de um componente em uma netlist SPICE.
        
        """

        with open(netlist_path, "r") as f:
            lines = f.readlines()

        updated_lines = []
        component_found = False

        for line in lines:
            stripped = line.strip()

            # Mantém comentários e linhas vazias
            if stripped.startswith("*") or stripped == "":
                updated_lines.append(line)
                continue

            parts = stripped.split()

            # Se não é o componente alvo, mantemos a linha
            if parts[0] != component_name:
                updated_lines.append(line)
                continue

            # Aqui sabemos que é o componente correto → substitui valor
            if len(parts) >= 4:
                parts[-1] = str(new_value)
                updated_line = " ".join(parts) + "\n"
                updated_lines.append(updated_line)
                component_found = True
                continue

            # Caso raro: componente sem valor → erro
            raise ValueError(f"Linha inválida para componente '{component_name}': {line}")

        if not component_found:
            raise ValueError(f"Componente '{component_name}' não encontrado na netlist.")

        with open(netlist_path, "w") as f:
            f.writelines(updated_lines)


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
