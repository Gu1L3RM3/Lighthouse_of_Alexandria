from abc import ABC, abstractmethod
from typing import Dict, Type, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from core.managers.entity_manager import EntityManager

class Component(ABC):
    
    def copy(self) -> "Component":
       
        return copy.deepcopy(self)


class Entity:
    _next_id = 1

    def __init__(self):
        self.id: int = Entity._next_id
        Entity._next_id += 1
        self.components: Dict[Type[Component], Component] = {}

    def add(self, *components: Component):
        for comp in components:
            self.components[type(comp)] = comp

    def remove(self, comp_type: Type[Component]):
        if comp_type in self.components:
            del self.components[comp_type]

    def has(self, comp_type: Type[Component]) -> bool:
        return comp_type in self.components
    
    def get(self, comp_type: Type[Component]):
        return self.components.get(comp_type)

    def copy(self) -> "Entity":
        new_entity = Entity()
        for comp in self.components.values():
            new_entity.add(comp.copy())
        return new_entity


class System(ABC):
    @abstractmethod
    def update(self, entity_mn: 'EntityManager', dt: float):
        pass
