import pygame
from pygame import Surface
from core.ui.widgets.widget import Widget
from core.managers.resource_manager import ResourceManager
class FPSWidget(Widget):
    def __init__(self,  font_size: int = 20, pos=(10, 10), color=(255, 255, 0)):
        super().__init__()
        resource_mn=ResourceManager.get()
        self.font=resource_mn.load_font("PressStart2P-Regular.ttf",font_size)
        self.pos = pos
        self.color = color
        
        self.display_fps = 0
        self._cached_text_surface: Surface | None = None
        self._cached_label: str = ""

        
        self._update_interval = 0.5 
        self._time_since_update = 0.0
        self._frame_count = 0

    def update(self, dt: float):

        if dt <= 0:
            return

        self._time_since_update += dt
        self._frame_count += 1

        if self._time_since_update >= self._update_interval:
            self.display_fps = self._frame_count / self._time_since_update
            
            self._time_since_update = 0.0
            self._frame_count = 0

    def draw(self,screen:Surface):
        label = f"FPS: {int(self.display_fps)}"
        if self._cached_text_surface is None or label != self._cached_label:
            self._cached_label = label
            self._cached_text_surface = self.font.render(label, True, self.color)
        text_surface = self._cached_text_surface
        
        bg_rect = text_surface.get_rect()
        bg_rect.topleft = self.pos
        pygame.draw.rect(screen, (0, 0, 0), bg_rect.inflate(4, 4))

        screen.blit(text_surface, self.pos)
