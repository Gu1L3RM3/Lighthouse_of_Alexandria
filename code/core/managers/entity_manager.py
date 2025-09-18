from typing import Type, Dict, List, Optional, Callable
from core.ecs import Component, Entity
from entities.player import Player
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.collider import Collider



class EntityManager:
    def __init__(self):
        self._entities: Dict[int, Entity] = {}
    @property
    def entities(self):
        return self._entities

    def create(self, *components: Component) -> Entity:
        entity = Entity()
        self.add_entity(entity, *components)
        return entity

    def add_entity(self, entity: Entity, *components: Component):
        self._entities[entity.id] = entity
        entity.add(*components)

    def add_component(self, entity: Entity, component: Component):
        entity.add(component)

    def remove_component(self, entity: Entity, comp_type: Type[Component]):
        entity.remove(comp_type)



    def remove_entity(self, entity: Entity):
        if entity.id in self._entities:
            del self._entities[entity.id]
    

    def get_player(self)->Player:
        for e in self._entities.values():
            if isinstance(e,Player):
                return e

    def get_entities(self) -> List[Entity]:
        
        return list(self._entities.values())
    

    

    def get_entity_by_id(self, eid: int) -> Optional[Entity]:
        return self._entities.get(eid)

    def get_entities_with(
        self,
        *comp_types: Type[Component],
        filter: Optional[Callable[[Entity], bool]] = None
    ) -> List[Entity]:
        

        index: Dict[Type[Component], set[Entity]] = {}
        for ct in comp_types:
            index[ct] = {e for e in self._entities.values() if e.has(ct)}
            if not index[ct]:
                return []  

        sorted_sets = sorted(index.values(), key=len)
        result_set = sorted_sets[0].copy()
        for s in sorted_sets[1:]:
            result_set.intersection_update(s)

        if filter:
            result_set = {e for e in result_set if filter(e)}

        return list(result_set)