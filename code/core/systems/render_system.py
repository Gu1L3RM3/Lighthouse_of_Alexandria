import pygame
from core.ecs import System,Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.camera import Camera
from core.managers.entity_manager import EntityManager
from core.settings import RED,BLUE
class RenderSystem(System):
    def __init__(self, screen: pygame.Surface, camera: Camera, entity_mn: EntityManager):
        self.screen = screen
        self.camera = camera
        self.entity_mn = entity_mn
    
    def update(self, entity_mn, dt):
        self.camera.update()
        
    def _draw_collider(self,entity:Entity,pos:Position):
        if entity.has(Collider):
            col: Collider = entity.get(Collider)
                    
            collider_world_rect = col.get_rect(pos.x, pos.y)
                    
            collider_draw_rect = self.camera.apply(collider_world_rect)
                    
            pygame.draw.rect(self.screen, RED, collider_draw_rect, 1)
    def _draw_rect_sprites(self,spr:Sprite):
        rect=spr.rect
        rect_draw=self.camera.apply(rect)
        pygame.draw.rect(self.screen,BLUE,rect_draw,1)

    def draw(self):
        entities  = self.entity_mn.get_entities_with(Position, Sprite)

        viewport = self.camera.viewport

        for entity in entities:
            pos: Position = entity.get(Position)
            spr: Sprite = entity.get(Sprite)

            spr.rect.topleft = (pos.x + spr.offset_x, pos.y + spr.offset_y)

            if viewport.colliderect(spr.rect):
                draw_rect = self.camera.apply(spr.rect)
                self.screen.blit(spr.image, draw_rect)

                self._draw_collider(entity,pos)
                self._draw_rect_sprites(spr)

                
