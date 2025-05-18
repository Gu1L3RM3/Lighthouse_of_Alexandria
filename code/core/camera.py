
from pygame import Rect,Surface

from core.components.position import Position
from core.ecs import Entity
class Camera:
    def __init__(self,
                 screen:Surface,
                 world_width:int,
                 world_height:int
                 ):
        self.screen=screen
        w,h=self.screen.get_size()
        self.viewport=Rect(0,0,w,h)
        self.world_width=world_width
        self.world_height=world_height
        self._target:Entity|None=None
    @property
    def target(self)->Entity|None:
        return self._target
    @target.setter
    def follow(self,entity:Entity):
        if not entity.has(Position):
            raise ValueError("Target must has a Position Component")
        self._target=entity
    
    def update(self):
        if self._target is None:
            return 
        position:Position=self._target.get(Position) 
        pos=position.pos

        x = int(pos.x - self.viewport.w  / 2)
        y = int(pos.y - self.viewport.h / 2)
        x = max(0, min(x, self.world_width  - self.viewport.w))
        y = max(0, min(y, self.world_height - self.viewport.h))
        
        self.viewport.topleft=(x,y)
    def apply(self,target_rect:Rect)->Rect:
        return target_rect.move(-self.viewport.x,-self.viewport.y)