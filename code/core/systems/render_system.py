import pygame
from pygame import Vector2, Rect, Surface
from core.ecs import System, Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.components.area_trigger import AreaTrigger
from core.components.always_on_top import AlwaysOnTop
from core.camera import Camera
from core.managers.entity_manager import EntityManager
from core.components.label_component import LabelComponent
from core.settings import RED, BLUE


class RenderSystem(System):
    def __init__(self, screen: pygame.Surface, camera: Camera, entity_mn: EntityManager):
        self.screen = screen
        self.camera = camera
        self.entity_mn = entity_mn
        self.debug_mode = False

    def update(self, entity_mn, dt):
        self.camera.update()
    def _draw_camera_viewport(self):
        
        viewport_color = (255, 255, 0) 
        
        pygame.draw.rect(self.screen, viewport_color, self.camera.viewport,1)

    def _draw_dialogues_areas(self,entity:Entity,pos:Position,scale:float):
        if entity.has(Dialogue):
            dialogue:Dialogue=entity.get(Dialogue)
            area = dialogue.get_area(pos.x,pos.y)

            area_scaled = Rect(
                area.x * scale,
                area.y * scale,
                area.width * scale,
                area.height * scale,
            )
            area_draw_rect = self.camera.apply(area_scaled)
            pygame.draw.rect(self.screen, RED, area_draw_rect,1)

            
        

    def _draw_collider(self, entity: Entity, pos: Position, scale: float):
        
        if entity.has(Collider):
            col: Collider = entity.get(Collider)
            collider_world_rect = col.get_rect(pos.x, pos.y)

            
            collider_scaled = Rect(
                collider_world_rect.x * scale,
                collider_world_rect.y * scale,
                collider_world_rect.width * scale,
                collider_world_rect.height * scale,
            )

            collider_draw_rect = self.camera.apply(collider_scaled)
            pygame.draw.rect(self.screen, RED, collider_draw_rect, 1)
  
    def _draw_area_triggers(self, entity: Entity, pos: Position, scale: float):
        """Desenha a área de trigger (debug) levando em conta posição e escala."""
        if not entity.has(AreaTrigger):
            return
        
        area_trigger: AreaTrigger = entity.get(AreaTrigger)
        area_rect = area_trigger.area

        

    
        area_scaled = Rect(
            area_rect.x * scale,
            area_rect.y * scale,
            area_rect.width * scale,
            area_rect.height *scale,
        )

        
        area_draw_rect = self.camera.apply(area_scaled)

        
        color = (0, 255, 0) if area_trigger.active else (100, 100, 100)

        
        pygame.draw.rect(self.screen, color, area_draw_rect, 2)

    def _draw_rect_sprites(self, spr: Sprite, scale: float):
        rect = spr.rect
        rect_scaled = Rect(
            rect.x * scale,
            rect.y * scale,
            rect.width * scale,
            rect.height * scale,
        )
        rect_draw = self.camera.apply(rect_scaled)
        pygame.draw.rect(self.screen, BLUE, rect_draw, 1)

    def draw(self, from_center_pos=False, scale: float = 1.0):
        entities = self.entity_mn.get_entities_with(Position, Sprite)
        viewport = self.camera.viewport

        entities.sort(key=lambda e: e.has(AlwaysOnTop))

        for entity in entities:
            self._draw_entity(entity, from_center_pos, viewport, scale)

        self._draw_debug_info(entities,scale)

    def _draw_debug_info(self,entities:list[Entity],scale:float):
        if not self.debug_mode:
            return
        for entity in entities:
            pos: Position = entity.get(Position)
            self._draw_collider(entity, pos, scale)
            self._draw_area_triggers(entity, pos, scale)
            self._draw_dialogues_areas(entity, pos, scale)
        self._draw_camera_viewport()

    def _draw_entity(self, entity, from_center_pos, viewport, scale: float):
        pos: Position = entity.get(Position)
        spr: Sprite = entity.get(Sprite)

        if from_center_pos:
            spr.rect.center = (pos.x, pos.y)
        else:
            spr.rect.topleft = (pos.x + spr.offset_x, pos.y + spr.offset_y)


        scaled_entity_rect = Rect(
            spr.rect.x * scale,
            spr.rect.y * scale,
            spr.rect.width * scale,
            spr.rect.height * scale
        )

        if not viewport.colliderect(scaled_entity_rect):
            return

        image = spr.get_image_for_drawing(scale)
        draw_rect = self.camera.apply(scaled_entity_rect)


        self.screen.blit(image, draw_rect)
        self._draw_label(entity, draw_rect, scale)
        

    def _draw_label(self, entity: Entity, draw_rect: Rect, scale: float):
        if not entity.has(LabelComponent):
            return

        spr: Sprite = entity.get(Sprite)
        label_comp: LabelComponent = entity.get(LabelComponent)
        comp_center = Vector2(draw_rect.center)

        for label_data in label_comp.rendered_labels:
            rotated_offset = label_data['base_offset'].rotate(-spr.angle)
            label_pos = comp_center + rotated_offset * scale
            text_surface: Surface = label_data['surface']

        
            tw, th = text_surface.get_size()
            text_surface = pygame.transform.scale(
                text_surface, (int(tw * scale), int(th * scale))
            )

            text_rect = text_surface.get_rect(center=label_pos)
            self.screen.blit(text_surface, text_rect)
