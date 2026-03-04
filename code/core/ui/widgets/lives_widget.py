import math
import pygame
from pygame import Surface

from core.ui.widgets.widget import Widget
from core.managers.resource_manager import ResourceManager
from core.managers.life_manager import LifeManager


class LivesWidget(Widget):
    def __init__(self, pos=(10, 44)):
        super().__init__()
        self.pos = pos
        self.resources = ResourceManager.get()
        self.life_manager = LifeManager.get()
        self.font = self.resources.load_font("PressStart2P-Regular.ttf", 12)
        self.prev_lives = self.life_manager.current_lives
        self.pulse_timer = 0.0

    def update(self, dt):
        current_lives = self.life_manager.current_lives
        if current_lives < self.prev_lives:
            self.pulse_timer = 0.35
        self.prev_lives = current_lives
        self.pulse_timer = max(0.0, self.pulse_timer - dt)

    def draw(self, surface: Surface):
        lives = self.life_manager.current_lives
        max_lives = self.life_manager.max_lives
        text = self.font.render(f"TENTATIVAS x{lives}", True, (240, 214, 140))
        text_rect = text.get_rect(topleft=self.pos)

        pad_x, pad_y = 8, 6
        panel_rect = pygame.Rect(
            text_rect.left - pad_x,
            text_rect.top - pad_y,
            text_rect.width + 16 + max_lives * 14,
            text_rect.height + 12,
        )
        pygame.draw.rect(surface, (0, 0, 0), panel_rect, border_radius=6)
        pygame.draw.rect(surface, (158, 126, 76), panel_rect, width=2, border_radius=6)
        surface.blit(text, text_rect)

        pulse_scale = 1.0 + 0.28 * math.sin(self.pulse_timer * 26.0) if self.pulse_timer > 0 else 1.0
        icon_base_x = text_rect.right + 10
        icon_y = panel_rect.centery
        for i in range(max_lives):
            color = (241, 196, 108) if i < lives else (88, 80, 66)
            radius = 4
            if i == lives and self.pulse_timer > 0:
                radius = int(radius * pulse_scale)
            pygame.draw.circle(surface, color, (icon_base_x + i * 14, icon_y), max(2, radius))
