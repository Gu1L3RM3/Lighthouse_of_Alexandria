import pygame
from pygame import Vector2, Rect, Surface
from core.ecs import System, Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.components.area_trigger import AreaTrigger
from core.components.always_on_top import AlwaysOnTop
from core.components.render_layer import RenderLayer
from core.components.depth_anchor import DepthAnchor
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
        self._scaled_text_cache: dict[tuple[int, int], Surface] = {}
        self._scaled_text_cache_limit = 1024

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

    def _sync_sprite_rect(self, entity: Entity, from_center_pos: bool):
        pos: Position = entity.get(Position)
        spr: Sprite = entity.get(Sprite)
        if from_center_pos:
            spr.rect.center = (pos.x, pos.y)
        else:
            spr.rect.topleft = (pos.x + spr.offset_x, pos.y + spr.offset_y)

    def _world_viewport(self, viewport: Rect, scale: float) -> Rect:
        if scale <= 0:
            return Rect(viewport)
        inv = 1.0 / scale
        return Rect(
            int(viewport.x * inv),
            int(viewport.y * inv),
            int(viewport.width * inv) + 2,
            int(viewport.height * inv) + 2,
        )

    def draw(self, from_center_pos=False, scale: float = 1.0):
        entities = self.entity_mn.get_entities_with(Position, Sprite)
        viewport = self.camera.viewport
        world_viewport = self._world_viewport(viewport, scale)
        visible_entities: list[Entity] = []

        for entity in entities:
            self._sync_sprite_rect(entity, from_center_pos)
            spr: Sprite = entity.get(Sprite)
            if spr.rect.colliderect(world_viewport):
                visible_entities.append(entity)

        visible_entities.sort(key=self._render_sort_key)

        for entity in visible_entities:
            self._draw_entity(entity, viewport, scale)

        self._draw_debug_info(visible_entities,scale)

    def _render_sort_key(self, entity: Entity):
        layer_value = self._get_layer_value(entity)
        depth_y = self._get_depth_y(entity)
        return (layer_value, depth_y, entity.id)

    def _get_layer_value(self, entity: Entity) -> int:
        if entity.has(RenderLayer):
            layer: RenderLayer = entity.get(RenderLayer)
            return layer.value

        # Compatibilidade com cenas antigas que ainda usam AlwaysOnTop.
        if entity.has(AlwaysOnTop):
            return RenderLayer.OVERLAY

        return RenderLayer.ACTOR

    def _get_depth_y(self, entity: Entity) -> int:
        pos: Position = entity.get(Position)
        if entity.has(DepthAnchor):
            anchor: DepthAnchor = entity.get(DepthAnchor)
            return int(pos.y + anchor.offset_y)

        if entity.has(Collider):
            col: Collider = entity.get(Collider)
            return int(pos.y + col.offset_y + col.height)

        if entity.has(Sprite):
            spr: Sprite = entity.get(Sprite)
            return int(pos.y + spr.rect.height)

        return int(pos.y)

    def _draw_debug_info(self,entities:list[Entity],scale:float):
        if not self.debug_mode:
            return
        for entity in entities:
            pos: Position = entity.get(Position)
            self._draw_collider(entity, pos, scale)
            self._draw_area_triggers(entity, pos, scale)
            self._draw_dialogues_areas(entity, pos, scale)
        self._draw_camera_viewport()

    def _draw_entity(self, entity, viewport, scale: float):
        spr: Sprite = entity.get(Sprite)


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
        
    def _get_scaled_label_surface(self, base_surface: Surface, scale: float) -> Surface:
        if scale == 1.0:
            return base_surface
        key = (id(base_surface), int(scale * 1000))
        cached = self._scaled_text_cache.get(key)
        if cached is not None:
            return cached

        tw, th = base_surface.get_size()
        scaled_surface = pygame.transform.scale(
            base_surface, (int(tw * scale), int(th * scale))
        )
        if len(self._scaled_text_cache) >= self._scaled_text_cache_limit:
            self._scaled_text_cache.clear()
        self._scaled_text_cache[key] = scaled_surface
        return scaled_surface

    def _draw_label(self, entity: Entity, draw_rect: Rect, scale: float):
        if not entity.has(LabelComponent):
            return

        spr: Sprite = entity.get(Sprite)
        label_comp: LabelComponent = entity.get(LabelComponent)
        comp_center = Vector2(draw_rect.center)

        for label_data in label_comp.rendered_labels:
            rotated_offset = label_data['base_offset'].rotate(-spr.angle)
            label_pos = comp_center + rotated_offset * scale
            text_surface: Surface = self._get_scaled_label_surface(label_data['surface'], scale)

            text_rect = text_surface.get_rect(center=label_pos)
            self.screen.blit(text_surface, text_rect)
