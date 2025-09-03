import pygame
from typing import Callable, Union
from core.managers.resource_manager import ResourceManager
from core.settings import *
from ui.widgets.widget import Widget

class TypewriterEffect(Widget):
    """
    Cria e gerencia um efeito de digitação para um texto.
    O parâmetro 'position' define o PONTO CENTRAL do texto final.
    """
    def __init__(self,
                 position: tuple[int, int],
                 text: str,
                 font_name: str,
                 font_size: int,
                 font_color: tuple[int, int, int] = (255, 255, 255),
                 speed: int = 20,
                 sound_name: Union[str, None] = None,
                 on_finish: Union[Callable, None] = None):
        
        self.rm = ResourceManager.get()
        self.center_position = position 
        self.font_color = font_color
        self.speed = speed
        self.on_finish = on_finish

        self.font = self.rm.load_font(font_name, font_size)
        self.sound = self.rm.load_sound(sound_name) if sound_name else None

        # Estado do efeito
        self._full_text = ""
        self._current_text = ""
        self._current_index = 0
        self.draw_position = (0, 0) 
        
        self.set_text(text)

    def _calculate_start_position(self):
       
        text_surface = self.font.render(self._full_text, True, self.font_color)
        
        text_rect = text_surface.get_rect(center=self.center_position)
        
        self.draw_position = text_rect.topleft

    def update(self,dt):
        if self.finished:
            return

        now = pygame.time.get_ticks()
        if now - self._last_update > self._interval:
            self._last_update = now
            if self._current_index < len(self._full_text):
                self._current_text += self._full_text[self._current_index]
                self._current_index += 1
                if self.sound:
                    self.sound.play()
            else:
                self.finished = True
                if self.on_finish:
                    self.on_finish()

    def draw(self, surface: pygame.Surface):
       
        rendered_text = self.font.render(self._current_text, True, self.font_color)
        
        
        surface.blit(rendered_text, self.draw_position)

    def skip(self):
        if not self.finished:
            self._current_text = self._full_text
            self._current_index = len(self._full_text)
            self.finished = True
            if self.on_finish:
                self.on_finish()
    
    def set_text(self, new_text: str):
        self._full_text = new_text
        self._current_text = ""
        self._current_index = 0
        self.finished = False
        self._interval = 1000 / self.speed
        self._last_update = pygame.time.get_ticks()
        
      
        self._calculate_start_position()