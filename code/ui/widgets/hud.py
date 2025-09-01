import pygame
from core.managers.day_night_manager import DayNightManager
from core.managers.resource_manager import ResourceManager
from ui.widgets.widget import Widget
from ui.widgets.clock import Clock
from ui.widgets.fps_widget import FPSWidget
class HUD(Widget):
    """
    Sistema dedicado a desenhar a Interface do Usuário (HUD),
    como o relógio, barra de vida, etc. Os elementos desenhados
    aqui são fixos na tela e não seguem a câmera.
    """
    def __init__(self, screen: pygame.Surface, day_night_manager: DayNightManager):
        self.screen=screen
        self.clock=Clock(day_night_manager)
        self.fps=FPSWidget(self.screen)

    def update(self, dt):
        self.fps.update(dt)
        self.clock.update(dt)

    def draw(self,surface):
        self.fps.draw()
        self.clock.draw(surface)

    