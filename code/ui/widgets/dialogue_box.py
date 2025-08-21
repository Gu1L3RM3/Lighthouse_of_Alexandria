# No arquivo: ui/widgets/dialogue_box.py

import pygame
from ui.widgets.widget import Widget
from core.components.dialogue import Dialogue

class DialogueBoxWidget(Widget):
    def __init__(self, dialogue_component: Dialogue,):
        self.dialogue = dialogue_component
    def update(self, dt):
        pass
    def draw(self, surface: pygame.Surface):
        if not self.dialogue.active or not self.dialogue.dialog_box_rect:
            return

        pygame.draw.rect(surface, (10, 20, 40), self.dialogue.dialog_box_rect, border_radius=8)
        pygame.draw.rect(surface, (200, 220, 255), self.dialogue.dialog_box_rect, 2, border_radius=8)
        
        if self.dialogue.typewriter:
            self.dialogue.typewriter.draw(surface)