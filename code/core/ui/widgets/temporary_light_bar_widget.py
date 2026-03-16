import pygame

from core.ui.widgets.widget import Widget


class TemporaryLightBarWidget(Widget):
    def __init__(self, screen_size: tuple[int, int], level_scene):
        super().__init__()
        self.level_scene = level_scene
        screen_w, screen_h = screen_size
        self._screen_h = screen_h
        self.outer_rect = pygame.Rect(12, screen_h - 40, min(220, max(140, screen_w // 4)), 12)

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        ratio = self.level_scene.get_temporary_light_ratio()
        if ratio <= 0:
            return

        self.outer_rect.y = self._screen_h - self._bottom_offset()

        pygame.draw.rect(surface, (18, 20, 26), self.outer_rect, border_radius=5)
        pygame.draw.rect(surface, (245, 232, 165), self.outer_rect, width=1, border_radius=5)

        fill = self.outer_rect.copy()
        fill.width = max(1, int(self.outer_rect.width * ratio))

        if ratio > 0.5:
            color = (255, 232, 120)
        elif ratio > 0.25:
            color = (255, 188, 92)
        else:
            color = (255, 110, 84)

        pygame.draw.rect(surface, color, fill, border_radius=5)

    def _bottom_offset(self) -> int:
        stealth_ratio = 0.0
        if hasattr(self.level_scene, "phantom_ai_system"):
            get_ratio = getattr(self.level_scene.phantom_ai_system, "get_stealth_ratio", None)
            if callable(get_ratio):
                stealth_ratio = get_ratio()

        return 58 if stealth_ratio > 0 else 40
