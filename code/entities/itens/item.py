from core.ecs import Entity
from abc import abstractmethod ,ABC
from pygame import Rect
from core.components.area_trigger import AreaTrigger
class Item(Entity,ABC):

    def __init__(self,x:int,y:int,active:bool,props:dict):
        super().__init__()
        self.area_trigger=Rect(x,y,48,48)

    @abstractmethod
    def on_collect(self,id:int):
        pass

    

