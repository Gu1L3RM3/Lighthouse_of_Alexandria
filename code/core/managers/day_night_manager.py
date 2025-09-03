import pygame
from core.settings import *
class DayNightManager:
    
    
   

    # Pontos-chave do ciclo (Hora, Cor)
    
    KEY_FRAMES = [
        (0,  NIGHT_COLOR),
        (4,  NIGHT_COLOR),    
        (6,  DAWN_COLOR),    
        (8,  DAY_COLOR),     
        (17, DAY_COLOR),    
        (18, DUSK_COLOR),    
        (21, NIGHT_COLOR),   
        (24, NIGHT_COLOR)    
    ]

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.time_of_day = 8.0  

    def _lerp_color(self, color1, color2, factor: float) -> tuple:
        """Interpola linearmente entre duas cores (R, G, B, A)."""
        r = color1[0] + (color2[0] - color1[0]) * factor
        g = color1[1] + (color2[1] - color1[1]) * factor
        b = color1[2] + (color2[2] - color1[2]) * factor
        a = color1[3] + (color2[3] - color1[3]) * factor
        return int(r), int(g), int(b), int(a)

    def update(self, dt: float):
        GAME_HOUR_DURATION = 48.0  
        game_hours_per_second = 1 / GAME_HOUR_DURATION

        self.time_of_day = (self.time_of_day + game_hours_per_second * dt) % 24

        
        prev_frame = self.KEY_FRAMES[0]
        next_frame = self.KEY_FRAMES[1]
        for i in range(len(self.KEY_FRAMES) - 1):
            if self.KEY_FRAMES[i][0] <= self.time_of_day < self.KEY_FRAMES[i+1][0]:
                prev_frame = self.KEY_FRAMES[i]
                next_frame = self.KEY_FRAMES[i+1]
                break

        prev_time, prev_color = prev_frame
        next_time, next_color = next_frame

        phase_duration = next_time - prev_time
        time_in_phase = self.time_of_day - prev_time
        
        progress = time_in_phase / phase_duration if phase_duration > 0 else 0

        current_color = self._lerp_color(prev_color, next_color, progress)
        self.overlay.fill(current_color)

    def draw(self):
        self.screen.blit(self.overlay, (0, 0))

    def set_time(self, hour: float):
        self.time_of_day = hour % 24