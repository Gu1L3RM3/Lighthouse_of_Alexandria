import pygame
from pygame import Surface
from core.ecs import System
from core.components.light_component import LightComponent
from core.components.position import Position
from core.components.sprite import Sprite

class LightSystem(System):
    def __init__(self, screen: Surface, camera, enabled: bool = True, ambient_alpha: int = 255, debug: bool = False):
        super().__init__()
        self.screen = screen
        self.camera = camera
        self.enabled = enabled
        self.initial_enabled = enabled
        self.ambient_alpha = max(0, min(255, ambient_alpha))
        self.debug = debug

    def toggle(self):
        self.enabled = not self.enabled

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)

    def turn_on(self):
        # "Luz ligada" significa remover a escuridao global.
        self.enabled = False

    def turn_off(self):
        self.enabled = True

    def _entity_screen_center(self, entity):
        
        pos: Position = entity.get(Position)
        spr: Sprite = entity.get(Sprite)

        scale = getattr(self.camera, "scale", 1.0)
        viewport = getattr(self.camera, "viewport", None)
        cam_x = viewport.x if viewport is not None else 0
        cam_y = viewport.y if viewport is not None else 0

        world_cx = pos.x + (spr.rect.width / 2.0)
        world_cy = pos.y + (spr.rect.height / 2.0)

        screen_x = int(world_cx * scale - cam_x)
        screen_y = int(world_cy * scale - cam_y)
        return screen_x, screen_y

    def light(self, entities_with_light: list):
        if not self.enabled:
            return None

        w, h = self.screen.get_size()
        darkness = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        darkness.fill((0, 0, 0, self.ambient_alpha))

        for entity in entities_with_light:
            try:
                light_comp: LightComponent = entity.get(LightComponent)
                if not getattr(light_comp, "light_on", True):
                    continue
                screen_x, screen_y = self._entity_screen_center(entity)
                radius = int(getattr(light_comp, "radius", 150) * getattr(self.camera, "scale", 1.0))
            except Exception:
                continue

            pygame.draw.circle(darkness, (0, 0, 0, 0), (screen_x, screen_y), radius)

            border_alpha =  60
            if border_alpha > 0:
                pygame.draw.circle(darkness, (0, 0, 0, border_alpha), (screen_x, screen_y), radius, width=max(1, int(radius * 0.08)))

            if self.debug:
                pygame.draw.circle(self.screen, (255, 0, 0), (screen_x, screen_y), 3)

        return darkness

    def update(self, entity_mn, dt):
        if not self.enabled:
            return

        entities_with_light = entity_mn.get_entities_with(LightComponent)
        if not entities_with_light:
            return

        darkness = self.light(entities_with_light)
        if darkness:
            self.screen.blit(darkness, (0, 0))
