from core.ecs import Component
from pygame import Surface

class Sprite(Component):
    def __init__(self,image: Surface,offset_x: float = 0,offset_y: float = 0): 
        self.image    = image
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.rect     = image.get_rect()