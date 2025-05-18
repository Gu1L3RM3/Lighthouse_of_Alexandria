import pygame 
from typing import List
from core.ecs import System , Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.camera import Camera
class RenderSystem(System):
    def __init__(self,screen:pygame.Surface,camera:Camera):
        self.screen=screen
        self.camera=camera
    #TODO: Verificar dt para camera
    def update(self, entities:List[Entity]):
        self.camera.update()
        for entity in entities:
            if entity.has(Position) and entity.has(Sprite):

                pos:Position=entity.get(Position)

                spr:Sprite= entity.get(Sprite)

                spr.rect.topleft=(pos.x+spr.offset_x,pos.y+spr.offset_y)

                draw_rect=self.camera.apply(spr.rect)
                

                self.screen.blit(spr.image,draw_rect)
