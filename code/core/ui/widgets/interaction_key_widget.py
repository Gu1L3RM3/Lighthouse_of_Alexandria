import pygame

from core.settings import FONT
from core.managers.language_service import LanguageService
from core.managers.input_manager import InputManager
from core.managers.resource_manager import ResourceManager
from core.ui.prompt_ui import draw_prompt_chip
from core.ui.widgets.widget import Widget


class InteractionKeyWidget(Widget):
    def __init__(self, screen_size: tuple[int, int], label: str | None = None):
        super().__init__()
        self.visible = False
        if label is None:
            label = LanguageService.get().get_ui_label("enter")
        self.label = label
        self.action = "interact"
        self.screen_w, self.screen_h = screen_size
        self.font_key = ResourceManager.get().load_font(FONT, 16)
        self.font_text = ResourceManager.get().load_font(FONT, 10)
        self.input_manager = InputManager.get()

    def set_visible(self, visible: bool):
        self.visible = visible

    def set_prompt(self, action: str, label: str):
        self.action = action
        self.label = label

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
        key_name = self.input_manager.get_prompt_button(self.action)
        draw_prompt_chip(surface, self.font_key, key_name, key_rect)

        text_surf = self.font_text.render(self.label, True, (245, 230, 170))
        text_pos = text_surf.get_rect(midright=(x - 8, y + box_h // 2 + 1))
        surface.blit(text_surf, text_pos)
