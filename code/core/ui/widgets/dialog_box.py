import pygame
from core.ui.widgets.widget import Widget
from core.components.dialogue import Dialogue
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.localization.scene_copy_catalog import SceneCopyCatalog
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
        hint_text = SceneCopyCatalog(LanguageService.get().get_current_language()).get("dialog_continue")
        hint_surf = self.hint_font.render(hint_text, True, (200, 220, 255))
        chip_w = max(34, self.hint_font.size(chip_label)[0] + 18)
        chip_h = max(24, self.hint_font.get_height() + 10)
        gap = 8
        box = self.dialogue.dialog_box_rect

        # Prioriza desenhar o hint fora da caixa, abaixo do box de dialogo.
        hint_rect = hint_surf.get_rect(
            topright=(box.right - 18, box.bottom + gap)
        )
        chip_rect = pygame.Rect(
            hint_rect.left - chip_w - 10,
            hint_rect.top,
            chip_w,
            chip_h,
        )

        # Se nao houver espaco abaixo, desenha fora da caixa por cima.
        if chip_rect.bottom > surface.get_height() - 4:
            hint_rect.top = max(4, box.top - hint_surf.get_height() - gap)
            chip_rect.top = max(4, hint_rect.top)
            chip_rect.bottom = chip_rect.top + chip_h

        draw_prompt_chip(surface, self.hint_font, chip_label, chip_rect)
        surface.blit(hint_surf, hint_rect)
