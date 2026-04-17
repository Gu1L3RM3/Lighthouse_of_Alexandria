import pygame

from core.ui.widgets.widget import Widget


class ComponentOverloadWidget(Widget):
    def __init__(self, screen_size: tuple[int, int], scene, anchor_pos: tuple[int, int] = (12, 162)):
        super().__init__()
        self.screen_size = screen_size
        self.scene = scene
        self.anchor_pos = anchor_pos

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        if not hasattr(self.scene, "get_component_overload_snapshot"):
            return

        snap = self.scene.get_component_overload_snapshot()
        if not snap or not snap.get("show", False):
            return

        x, y = self.anchor_pos
        panel_w = 272
        panel_h = 24
        panel = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(surface, (22, 24, 30), panel, border_radius=8)
        pygame.draw.rect(surface, (220, 196, 132), panel, width=2, border_radius=8)

        weight = float(snap.get("weight", 0.0))
        ratio = max(0.0, min(1.0, float(snap.get("ratio", 0.0))))

        bar_rect = pygame.Rect(x + 8, y + 5, panel_w - 16, 14)
        fill_w = int(bar_rect.width * ratio)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_rect.height)

        pygame.draw.rect(surface, (34, 38, 48), bar_rect, border_radius=5)
        if weight <= 0.0:
            fill_color = (90, 100, 118)
        else:
            r = int(54 + (220 - 54) * ratio)
            g = int(170 + (60 - 170) * ratio)
            b = int(130 + (60 - 130) * ratio)
            fill_color = (r, g, b)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=5)
        pygame.draw.rect(surface, (235, 221, 160), bar_rect, width=1, border_radius=5)
