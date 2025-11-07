from pygame import Rect, Surface, Vector2
from core.ecs import Entity
from core.components.position import Position

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

        # 1. Calcula a posição ideal da câmera para centralizar o jogador (considerando a escala)
        target_center_x = player_pos.x * self.scale
        target_center_y = player_pos.y * self.scale

        x = target_center_x - self.viewport.w / 2
        y = target_center_y - self.viewport.h / 2

        # 2. Verifica se o mundo é maior ou menor que a tela e ajusta a posição da câmera

        # Ajuste horizontal
        if self.world_width > self.viewport.w:
            # Mundo é LARGO: prende a câmera nas bordas do mundo
            x = max(0, min(x, self.world_width - self.viewport.w))
        else:
            # Mundo é ESTREITO: centraliza o mundo na tela
            x = (self.world_width - self.viewport.w) / 2

        # Ajuste vertical
        if self.world_height > self.viewport.h:
            # Mundo é ALTO: prende a câmera nas bordas do mundo
            y = max(0, min(y, self.world_height - self.viewport.h))
        else:
            # Mundo é BAIXO: centraliza o mundo na tela
            y = (self.world_height - self.viewport.h) / 2

        # 3. Define a posição final da câmera
        self.viewport.x = round(x)
        self.viewport.y = round(y)

    def update(self):
        """
        Atualiza a posição da câmera para seguir o alvo.
        Este método deve ser chamado a cada frame no loop principal do jogo.
        """
        if self._target is None:
            return
        self._center_on_target()

    def apply(self, target_rect: Rect) -> Rect:
        """
        Aplica o deslocamento da câmera a um retângulo (usado para renderização).
        Usa o viewport (que já está arredondado).
        """
        return target_rect.move(-self.viewport.x, -self.viewport.y)