from pygame import Rect, Surface, Vector2
from core.ecs import Entity
from core.components.position import Position
import random


class Camera:
    def __init__(self, screen: Surface, world_width: int, world_height: int):
        self.screen = screen

        w, h = self.screen.get_size()

        self.viewport = Rect(0, 0, w, h)
        self.position = Vector2(0, 0)

        self.world_width = world_width
        self.world_height = world_height

        self.scale = 1.0

        self._target: Entity | None = None

        # Screen shake state (render-only offset)
        self._shake_time_left = 0.0
        self._shake_duration = 0.0
        self._shake_intensity = 0.0
        self._shake_offset = Vector2(0, 0)

    @property
    def follow(self) -> Entity | None:
        return self._target

    @follow.setter
    def follow(self, entity: Entity):
        if not entity.has(Position):
            raise ValueError("Target must have a Position Component")
        self._target = entity
        self._center_on_target()

    def _center_on_target(self):
        if self._target is None:
            return

        player_pos: Position = self._target.get(Position)

        # 1. Calcula a posicao ideal da camera para centralizar o jogador (considerando a escala)
        target_center_x = player_pos.x * self.scale
        target_center_y = player_pos.y * self.scale

        x = target_center_x - self.viewport.w / 2
        y = target_center_y - self.viewport.h / 2

        # 2. Verifica se o mundo e maior ou menor que a tela e ajusta a posicao da camera

        # Ajuste horizontal
        if self.world_width > self.viewport.w:
            # Mundo e largo: prende a camera nas bordas do mundo
            x = max(0, min(x, self.world_width - self.viewport.w))
        else:
            # Mundo e estreito: centraliza o mundo na tela
            x = (self.world_width - self.viewport.w) / 2

        # Ajuste vertical
        if self.world_height > self.viewport.h:
            # Mundo e alto: prende a camera nas bordas do mundo
            y = max(0, min(y, self.world_height - self.viewport.h))
        else:
            # Mundo e baixo: centraliza o mundo na tela
            y = (self.world_height - self.viewport.h) / 2

        # 3. Define a posicao final da camera
        self.viewport.x = round(x)
        self.viewport.y = round(y)

    def update(self, dt: float = 0.0):
        """
        Atualiza a posicao da camera para seguir o alvo.
        Este metodo deve ser chamado a cada frame no loop principal do jogo.
        """
        if self._target is None:
            return
        self._center_on_target()
        self._update_shake(dt)

    def start_shake(self, duration: float = 0.18, intensity: float = 4.0):
        self._shake_duration = max(self._shake_duration, float(duration))
        self._shake_time_left = max(self._shake_time_left, float(duration))
        self._shake_intensity = max(self._shake_intensity, float(intensity))

    def _update_shake(self, dt: float):
        if self._shake_time_left <= 0:
            self._shake_offset.xy = (0, 0)
            self._shake_duration = 0.0
            self._shake_intensity = 0.0
            return

        self._shake_time_left = max(0.0, self._shake_time_left - max(0.0, dt))
        ratio = self._shake_time_left / max(0.001, self._shake_duration)
        amp = self._shake_intensity * ratio
        self._shake_offset.xy = (
            random.uniform(-amp, amp),
            random.uniform(-amp, amp),
        )

    @property
    def render_offset(self) -> tuple[int, int]:
        return (int(self._shake_offset.x), int(self._shake_offset.y))

    def apply(self, target_rect: Rect) -> Rect:
        """
        Aplica o deslocamento da camera a um retangulo (usado para renderizacao).
        Usa o viewport (ja arredondado).
        """
        return target_rect.move(
            -self.viewport.x + int(self._shake_offset.x),
            -self.viewport.y + int(self._shake_offset.y),
        )
