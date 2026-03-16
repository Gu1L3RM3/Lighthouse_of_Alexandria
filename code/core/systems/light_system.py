import pygame
from pygame import Surface
from core.ecs import System
from core.components.light_component import LightComponent
from core.components.position import Position
from core.components.sprite import Sprite

class LightSystem(System):
    def __init__(self, screen: Surface, camera, enabled: bool = True, ambient_alpha: int = 220, debug: bool = False):
        super().__init__()
        self.screen = screen
        self.camera = camera
        self.enabled = enabled
        self.initial_enabled = enabled
        self.ambient_alpha = max(0, min(255, ambient_alpha))
        self.current_alpha = float(self.ambient_alpha if enabled else 0)
        self._transition_active = False
        self._transition_elapsed = 0.0
        self._transition_duration = 0.0
        self._transition_from = float(self.current_alpha)
        self._transition_to = float(self.current_alpha)
        self._transition_target_enabled = enabled
        self.debug = debug

    def toggle(self):
        self.enabled = not self.enabled

    def set_enabled(self, enabled: bool, transition_seconds: float = 0.0):
        target_enabled = bool(enabled)
        duration = max(0.0, float(transition_seconds))

        if duration <= 0.0:
            self._transition_active = False
            self.enabled = target_enabled
            self.current_alpha = float(self.ambient_alpha if target_enabled else 0.0)
            return

        self._transition_active = True
        self._transition_elapsed = 0.0
        self._transition_duration = duration
        self._transition_from = float(self.current_alpha)
        self._transition_to = float(self.ambient_alpha if target_enabled else 0.0)
        self._transition_target_enabled = target_enabled
        # Mantem desenho ativo durante o fade.
        self.enabled = True

    def turn_on(self):
        # "Luz ligada" significa remover a escuridao global.
        self.set_enabled(False)

    def turn_off(self):
        self.set_enabled(True)

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
        darkness.fill((0, 0, 0, int(max(0, min(255, self.current_alpha)))))

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
        if self._transition_active:
            self._transition_elapsed += float(dt)
            t = min(1.0, self._transition_elapsed / max(1e-6, self._transition_duration))
            self.current_alpha = self._transition_from + (self._transition_to - self._transition_from) * t
            if t >= 1.0:
                self._transition_active = False
                self.current_alpha = float(self._transition_to)
                self.enabled = bool(self._transition_target_enabled)

        if not self.enabled:
            return

        entities_with_light = entity_mn.get_entities_with(LightComponent)
        if not entities_with_light:
            return

        darkness = self.light(entities_with_light)
        if darkness:
            self.screen.blit(darkness, (0, 0))
