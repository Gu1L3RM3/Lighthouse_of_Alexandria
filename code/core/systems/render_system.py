import pygame
from core.ecs import System,Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.always_on_top import AlwaysOnTop
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


    def draw(self, from_center_pos=False):
        entities = self.entity_mn.get_entities_with(Position, Sprite)
        viewport = self.camera.viewport

        normal_entities = []
        top_entities = []

        for entity in entities:
            if entity.has(AlwaysOnTop):
                top_entities.append(entity)
            else:
                normal_entities.append(entity)

        for entity in normal_entities:
            self._draw_entity(entity, from_center_pos, viewport)

        for entity in top_entities:
            self._draw_entity(entity, from_center_pos, viewport)


    def _draw_entity(self, entity, from_center_pos, viewport):
        pos: Position = entity.get(Position)
        spr: Sprite = entity.get(Sprite)

        if from_center_pos:
            spr.rect.center = (pos.x, pos.y)
        else:
            spr.rect.topleft = (pos.x + spr.offset_x, pos.y + spr.offset_y)

        if not viewport.colliderect(spr.rect):
            return

        draw_rect = self.camera.apply(spr.rect)
        self.screen.blit(spr.image, draw_rect)
