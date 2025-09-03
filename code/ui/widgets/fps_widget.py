import pygame
from ui.widgets.widget import Widget

class FPSWidget(Widget):
    def __init__(self, screen: pygame.Surface, font_size: int = 20, pos=(10, 10), color=(255, 255, 0)):
        super().__init__()
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", font_size)
        self.pos = pos
        self.color = color
        
        self.display_fps = 0

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

    def draw(self):
        text_surface = self.font.render(f"FPS: {int(self.display_fps)}", True, self.color)
        
        bg_rect = text_surface.get_rect()
        bg_rect.topleft = self.pos
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect.inflate(4, 4))

        self.screen.blit(text_surface, self.pos)