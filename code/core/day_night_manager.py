import pygame

class DayNightManager:
    """
    Gerencia um ciclo de dia e noite 
    """
    
    # Cores no formato (R, G, B, Alpha)
    DAWN_COLOR   = (255, 120, 50, 100) # Amanhecer: Laranja/Rosa
    DAY_COLOR    = (135, 206, 250, 0)  # Dia: Céu claro, sem overlay de escuridão
    DUSK_COLOR   = (255, 120, 50, 100) # Entardecer: Laranja/Rosa
    NIGHT_COLOR  = (10, 5, 40, 160)   # Noite: Azul escuro/Roxo

    # Pontos-chave do ciclo (Hora, Cor)
    
    KEY_FRAMES = [
        (0,  NIGHT_COLOR),
        (4,  NIGHT_COLOR),   # A noite profunda permanece até as 4h
        (6,  DAWN_COLOR),    # O pico do amanhecer é às 6h
        (8,  DAY_COLOR),     # O dia se estabelece completamente às 8h
        (17, DAY_COLOR),     # O dia claro dura até as 17h
        (19, DUSK_COLOR),    # O pico do entardecer é às 19h
        (21, NIGHT_COLOR),   # A noite se estabelece completamente às 21h
        (24, NIGHT_COLOR)    # Garante o loop para o próximo dia
    ]

    def __init__(self, screen: pygame.Surface, time_speed: float = 0.5):
        self.screen = screen
        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.time_of_day = 8.0  # Começa de manhã
        self.time_speed = time_speed

    def _lerp_color(self, color1, color2, factor: float) -> tuple:
        """Interpola linearmente entre duas cores (R, G, B, A)."""
        r = color1[0] + (color2[0] - color1[0]) * factor
        g = color1[1] + (color2[1] - color1[1]) * factor
        b = color1[2] + (color2[2] - color1[2]) * factor
        a = color1[3] + (color2[3] - color1[3]) * factor
        return int(r), int(g), int(b), int(a)

    def update(self, dt: float):
        """Atualiza a hora e calcula a cor do overlay por interpolação."""
        
        self.time_of_day = (self.time_of_day + self.time_speed * dt) % 24

        
        # Encontra os dois pontos-chave (keyframes) entre os quais a hora atual está
        prev_frame = self.KEY_FRAMES[0]
        next_frame = self.KEY_FRAMES[1]
        for i in range(len(self.KEY_FRAMES) - 1):
            if self.KEY_FRAMES[i][0] <= self.time_of_day < self.KEY_FRAMES[i+1][0]:
                prev_frame = self.KEY_FRAMES[i]
                next_frame = self.KEY_FRAMES[i+1]
                break

        prev_time, prev_color = prev_frame
        next_time, next_color = next_frame

        # Calcula o progresso (fator de 0.0 a 1.0) entre os dois keyframes
        phase_duration = next_time - prev_time
        time_in_phase = self.time_of_day - prev_time
        
        # Evita divisão por zero se a duração for 0
        progress = time_in_phase / phase_duration if phase_duration > 0 else 0

        # Interpola a cor atual baseada no progresso
        current_color = self._lerp_color(prev_color, next_color, progress)
        self.overlay.fill(current_color)

    def draw(self):
        """Desenha o overlay sobre a tela."""
        self.screen.blit(self.overlay, (0, 0))

    def set_time(self, hour: float):
        """Define manualmente a hora do dia."""
        self.time_of_day = hour % 24