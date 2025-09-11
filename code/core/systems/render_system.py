import pygame
from core.ecs import System
from core.components.position import Position
from core.components.sprite import Sprite
from core.camera import Camera
from core.managers.entity_manager import EntityManager
class RenderSystem(System):
    def __init__(self, screen: pygame.Surface, camera: Camera, entity_mn:EntityManager):
        self.screen = screen
        self.camera = camera
        self.entity_mn = entity_mn
    
    def update(self,entity_mn,dt):
        self.camera.update()
    

    def draw(self):

        entities = self.entity_mn.get_entities_with(Position, Sprite)
        viewport = self.camera.viewport

        for entity in entities:
            pos: Position = entity.get(Position)
            spr: Sprite = entity.get(Sprite)

            spr.rect.topleft = (pos.x + spr.offset_x, pos.y + spr.offset_y)

            if viewport.colliderect(spr.rect):
                draw_rect = spr.rect.move(-viewport.x, -viewport.y)
                self.screen.blit(spr.image, draw_rect)