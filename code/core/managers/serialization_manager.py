import json
from typing import Type
from core.ecs import Entity, Component
from entities.circuit_editor.eletric_components import *
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent


class SerializationManager:
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
    def reconstruct_entity(data: dict) -> Entity:
        """
        Reconstrói uma única entidade a partir de seu dicionário de dados.
        """
        entity_type_name = data['entity_type']
        EntityClass = SerializationManager.ENTITY_MAP.get(entity_type_name)

        if not EntityClass:
            raise ValueError(f"Tipo de entidade desconhecido: {entity_type_name}")

        new_entity = EntityClass.__new__(EntityClass)
        
        Entity.__init__(new_entity)

        for comp_data in data['components']:
            comp_type_name = comp_data['type']
            ComponentClass = SerializationManager.COMPONENT_MAP.get(comp_type_name)
            
            if not ComponentClass:
                raise ValueError(f"Tipo de componente desconhecido: {comp_type_name}")

            component_instance = ComponentClass.from_dict(comp_data)
            
            new_entity.add(component_instance)
        
        return new_entity
    @staticmethod
    def save_entities_to_json(entities: list[Entity], filepath: str):
        entities_data = [entity.to_dict() for entity in entities]
        with open(filepath, 'w') as f:
            json.dump(entities_data, f, indent=4)
        print(f"Circuito salva em {filepath}")
    @staticmethod
    def load_entities_from_json(filepath: str) -> list[Entity]:
        """Carrega uma lista de entidades de um arquivo JSON."""
        try:
            with open(filepath, 'r') as f:
                entities_data = json.load(f)
            
            reconstructed_entities = [SerializationManager.reconstruct_entity(data) for data in entities_data]
            print(f"Circuito carregada de {filepath}")
            return reconstructed_entities
        except FileNotFoundError:
            print(f"Arquivo de salvamento não encontrado: {filepath}")
            return []
    