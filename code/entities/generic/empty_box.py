import pygame
from core.components.sprite import Sprite
from core.components.position import Position
from core.ecs import Entity


class EmptyBox(Entity):
    def __init__(self,x,y,size:tuple[int,int],angle=0):
        super().__init__()
        self.angle= angle
        border_size = 4

        width  =  size[0]
        height =  size[1]
        surf   = pygame.Surface(size,pygame.SRCALPHA)
        surf.fill('red')
        surf.fill((0,0,0,0),
                  (border_size,border_size,width-2*border_size,height-2*border_size))
        self.add(
            Position(x,y),
            Sprite(image=surf,angle=self.angle)
        )

