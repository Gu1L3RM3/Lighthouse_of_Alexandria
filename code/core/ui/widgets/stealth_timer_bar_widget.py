import pygame

from core.ui.widgets.widget import Widget


class StealthTimerBarWidget(Widget):
    def __init__(self, screen_size: tuple[int, int], stealth_system):
        super().__init__()
        self.stealth_system = stealth_system
        screen_w, screen_h = screen_size
        self.outer_rect = pygame.Rect(12, screen_h - 24, min(180, max(120, screen_w // 5)), 10)

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        ratio = self.stealth_system.get_stealth_ratio()
        if ratio <= 0:
            return

        pygame.draw.rect(surface, (12, 14, 20), self.outer_rect, border_radius=4)
        pygame.draw.rect(surface, (154, 188, 220), self.outer_rect, width=1, border_radius=4)

        fill = self.outer_rect.copy()
        fill.width = max(1, int(self.outer_rect.width * ratio))
        color = (120, 210, 255) if ratio > 0.35 else (255, 180, 110)
        pygame.draw.rect(surface, color, fill, border_radius=4)
