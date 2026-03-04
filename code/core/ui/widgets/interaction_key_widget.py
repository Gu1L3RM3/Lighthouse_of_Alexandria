import pygame

from core.settings import FONT
from core.managers.resource_manager import ResourceManager
from core.ui.widgets.widget import Widget


class InteractionKeyWidget(Widget):
    def __init__(self, screen_size: tuple[int, int], label: str = "ENTRAR"):
        super().__init__()
        self.visible = False
        self.label = label
        self.screen_w, self.screen_h = screen_size
        self.font_key = ResourceManager.get().load_font(FONT, 16)
        self.font_text = ResourceManager.get().load_font(FONT, 10)

    def set_visible(self, visible: bool):
        self.visible = visible

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        pad = 12
        box_w = 40
        box_h = 40
        x = self.screen_w - box_w - pad
        y = self.screen_h - box_h - pad

        key_rect = pygame.Rect(x, y, box_w, box_h)
        pygame.draw.rect(surface, (24, 28, 36), key_rect, border_radius=8)
        pygame.draw.rect(surface, (235, 221, 160), key_rect, width=2, border_radius=8)

        key_surf = self.font_key.render("E", True, (245, 230, 170))
        key_pos = key_surf.get_rect(center=key_rect.center)
        surface.blit(key_surf, key_pos)

        text_surf = self.font_text.render(self.label, True, (245, 230, 170))
        text_pos = text_surf.get_rect(midright=(x - 8, y + box_h // 2 + 1))
        surface.blit(text_surf, text_pos)
