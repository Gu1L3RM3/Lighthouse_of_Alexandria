from pygame import Rect
from core.ecs import Component

class Collider(Component):
    def __init__(self,
                 width:int,
                 height:int,
                 offset_x:float=0,
                 offset_y:float=0):
        self.width=width
        self.height=height
        self.offset_x=offset_x
        self.offset_y=offset_y
    
    def get_rect(self,pos_x:float,pos_y:float):
        return Rect(
            int(pos_x+self.offset_x),
            int(pos_y+self.offset_y),
            self.width,
            self.height
        )
        