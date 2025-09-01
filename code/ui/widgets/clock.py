import pygame
from pygame import Surface 
from ui.widgets.widget import Widget
from core.managers.resource_manager import ResourceManager
from core.managers.day_night_manager import DayNightManager
from core.settings import *
class Clock(Widget):
    def __init__(self,day_night_manager: DayNightManager):
        
        self.rm=ResourceManager.get()
        self.dn_manager = day_night_manager
        self.hours:int=0
        self.minutes:int=0
        self.time_str="00:00"
        self.padding=10
        self.font = self.rm.load_font(FONT, 18)
        
    def update(self, dt):
        time_float=self.dn_manager.time_of_day
        self.hours = int(time_float)
        self.minutes = int((time_float - self.hours) * 60)
        self.time_str = f"{self.hours:02d}:{self.minutes:02d}" # f-string para formatar com zero à esquerda

    def draw(self, surface:Surface):
        text_surface =self.font.render(self.time_str,True,WHITE)
        bg_rect = pygame.Rect(
            0, 0, 
            text_surface.get_width() + self.padding* 2,
            text_surface.get_height() + self.padding* 2
            
        )
        bg_rect.topright = (surface.get_width() - 15, 15)
        text_rect = text_surface.get_rect(center=bg_rect.center)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect, border_radius=5) # Fundo preto semi-transparente
        surface.blit(text_surface, text_rect)