import pygame
from typing import Callable, Union
from core.resource_manager import ResourceManager
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
        self.center_position = position # Armazenamos a posição central desejada
        self.font_color = font_color
        self.speed = speed
        self.on_finish = on_finish

        self.font = self.rm.load_font(font_name, font_size)
        self.sound = self.rm.load_sound(sound_name) if sound_name else None

        # Estado do efeito
        self._full_text = ""
        self._current_text = ""
        self._current_index = 0
        self.draw_position = (0, 0) # Posição real do blit (top-left)
        
        # Chama set_text para configurar o texto inicial e calcular a posição
        self.set_text(text)

    def _calculate_start_position(self):
        """
        Calcula a posição do canto superior esquerdo (top-left) para que o texto
        completo fique centralizado na self.center_position.
        """
        # Renderiza o texto completo para obter suas dimensões
        text_surface = self.font.render(self._full_text, True, self.font_color)
        
        # Cria um retângulo com as dimensões do texto e define seu centro
        text_rect = text_surface.get_rect(center=self.center_position)
        
        # A posição de desenho será o canto superior esquerdo (topleft) deste retângulo
        self.draw_position = text_rect.topleft

    def update(self,dt):
        """Atualiza a lógica do efeito. Chame isso a cada frame no loop do jogo."""
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
        """Desenha o texto atual na superfície fornecida."""
        # Renderiza o texto que está sendo digitado
        rendered_text = self.font.render(self._current_text, True, self.font_color)
        
        # Usa a posição pré-calculada para o blit
        surface.blit(rendered_text, self.draw_position)

    def skip(self):
        """Pula o efeito e exibe o texto completo imediatamente."""
        if not self.finished:
            self._current_text = self._full_text
            self._current_index = len(self._full_text)
            self.finished = True
            if self.on_finish:
                self.on_finish()
    
    def set_text(self, new_text: str):
        """Reinicia o efeito com um novo texto e recalcula a posição."""
        self._full_text = new_text
        self._current_text = ""
        self._current_index = 0
        self.finished = False
        self._interval = 1000 / self.speed
        self._last_update = pygame.time.get_ticks()
        
        # Recalcula a posição de início para o novo texto
        self._calculate_start_position()