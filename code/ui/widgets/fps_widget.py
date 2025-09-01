import pygame
from ui.widgets.widget import Widget

class FPSWidget(Widget):
    def __init__(self, screen: pygame.Surface, font_size: int = 20, pos=(10, 10), color=(255, 255, 0)):
        super().__init__()
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", font_size)
        self.pos = pos
        self.color = color
        
        # O valor do FPS que será desenhado na tela
        self.display_fps = 0

        # --- Variáveis para cálculo estável ---
        # Com que frequência (em segundos) o display de FPS deve ser atualizado
        self._update_interval = 0.5 
        # Tempo acumulado desde a última atualização
        self._time_since_update = 0.0
        # Quantidade de frames contados desde a última atualização
        self._frame_count = 0

    def update(self, dt: float):
        """
        Acumula o tempo e os frames, e atualiza o FPS exibido
        quando o intervalo de tempo é atingido.
        """
        if dt <= 0:
            return

        self._time_since_update += dt
        self._frame_count += 1

        # Verifica se já passou o tempo do intervalo
        if self._time_since_update >= self._update_interval:
            # Calcula a média de FPS no intervalo
            self.display_fps = self._frame_count / self._time_since_update
            
            # Reseta os contadores para o próximo intervalo
            self._time_since_update = 0.0
            self._frame_count = 0

    def draw(self):
        """Desenha o valor de FPS estável na tela."""
        # Cria a superfície de texto com o valor estável (display_fps)
        text_surface = self.font.render(f"FPS: {int(self.display_fps)}", True, self.color)
        
        # Desenha um fundo preto para melhor legibilidade
        bg_rect = text_surface.get_rect()
        bg_rect.topleft = self.pos
        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect.inflate(4, 4))

        self.screen.blit(text_surface, self.pos)