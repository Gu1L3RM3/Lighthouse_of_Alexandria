import pygame
from core.ui.widgets.widget import Widget
from core.components.dialogue import Dialogue
from core.managers.input_manager import InputManager
from core.ui.prompt_ui import draw_prompt_chip

class DialogueBoxWidget(Widget):
    def __init__(self, dialogue_component: Dialogue,):
        self.dialogue = dialogue_component
        self.input_manager = InputManager.get()
        self.hint_font = pygame.font.Font(None, 22)
    def update(self, dt):
        
        if self.dialogue.typewriter:
            self.dialogue.typewriter.update(dt)

    def draw(self, surface: pygame.Surface):
        if not self.dialogue.active or not self.dialogue.dialog_box_rect:
            return

        pygame.draw.rect(surface, (10, 20, 40), self.dialogue.dialog_box_rect, border_radius=8)
        pygame.draw.rect(surface, (200, 220, 255), self.dialogue.dialog_box_rect, 2, border_radius=8)
        
        if self.dialogue.typewriter:
            self.dialogue.typewriter.draw(surface)

        chip_label = self.input_manager.get_prompt_button("interact")
        hint_surf = self.hint_font.render("continuar", True, (200, 220, 255))
        chip_w = max(34, self.hint_font.size(chip_label)[0] + 18)
        chip_h = max(24, self.hint_font.get_height() + 10)
        hint_rect = hint_surf.get_rect(
            bottomright=(self.dialogue.dialog_box_rect.right - 18, self.dialogue.dialog_box_rect.bottom - 12)
        )
        chip_rect = pygame.Rect(
            hint_rect.left - chip_w - 10,
            hint_rect.bottom - chip_h,
            chip_w,
            chip_h,
        )
        draw_prompt_chip(surface, self.hint_font, chip_label, chip_rect)
        surface.blit(hint_surf, hint_rect)
