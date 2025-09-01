from abc import ABC, abstractmethod
from typing import Dict,Type,List

class Component(ABC):
    """Marca : somente """
    pass



class Entity:
    '''Objeto do jogo'''
    _next_id=1
    def __init__(self):
        self.id:int=Entity._next_id
        Entity._next_id+=1

        self.components:Dict[Type[Component],Component]={}
    def add(self,*components: Component):
        for comp in components:
            self.components[type(comp)]=comp

    def remove(self,comp_type: Type[Component]):
        if comp_type in self.components:
            del self.components[comp_type]

    def has(self,comp_type:Type[Component])->bool:
        return comp_type in self.components
    
    def get(self,comp_type: Type[Component]):
        return self.components.get(comp_type)

class System(ABC):
    @abstractmethod
    def update(self,entities: List[Entity],dt:float):
        pass
