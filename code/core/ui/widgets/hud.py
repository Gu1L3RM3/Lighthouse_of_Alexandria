import pygame
from core.managers.day_night_manager import DayNightManager
from core.ui.widgets.widget import Widget
from core.ui.widgets import Clock,FPSWidget


class HUD(Widget):
    """
    Sistema dedicado a desenhar a Interface do Usuário (HUD),
    como o relógio, barra de vida, etc. Os elementos desenhados
    aqui são fixos na tela e não seguem a câmera.
    """
    def __init__(self, day_night_manager: DayNightManager):
        
        self.clock=Clock(day_night_manager)
        self.fps=FPSWidget()

    def update(self, dt):
        self.fps.update(dt)
        self.clock.update(dt)

    def draw(self,surface):
        self.fps.draw(surface)
        self.clock.draw(surface)

    