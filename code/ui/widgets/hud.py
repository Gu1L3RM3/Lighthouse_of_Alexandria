import pygame
from core.day_night_manager import DayNightManager
from core.resource_manager import ResourceManager
from ui.widgets.widget import Widget
from ui.widgets.clock import Clock
class HUD(Widget):
    """
    Sistema dedicado a desenhar a Interface do Usuário (HUD),
    como o relógio, barra de vida, etc. Os elementos desenhados
    aqui são fixos na tela e não seguem a câmera.
    """
    def __init__(self, screen: pygame.Surface, day_night_manager: DayNightManager):
        self.clock=Clock(day_night_manager)
        self.screen=screen
    def update(self, dt):
        self.clock.update(dt)

    def draw(self,surface):
        self.clock.draw(surface)

    