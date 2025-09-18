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

        self.position.x = player_pos.x - self.viewport.w / 2
        self.position.y = player_pos.y - self.viewport.h / 2

        if self.world_width <= self.viewport.w:
            self.position.x = (self.world_width - self.viewport.w) / 2
        else:
            self.position.x = max(0, min(self.position.x, self.world_width - self.viewport.w))

        if self.world_height <= self.viewport.h:
            self.position.y = (self.world_height - self.viewport.h) / 2
        else:
            self.position.y = max(0, min(self.position.y, self.world_height - self.viewport.h))
            
      
        self.viewport.x = round(self.position.x)
        self.viewport.y = round(self.position.y)

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