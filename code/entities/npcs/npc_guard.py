from pygame import Surface
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite

class GuardNPC(Entity):
    def __init__(self, x, y, props=None):
       super().__init__()
       image=Surface((16,16))
       image.fill((0,255,0))


     
       self.add(Position(x,y),
                Collider(16,16),
                Sprite(image)
                )
       self.props = props or {}
    
    def update(self, dt):
        # Futuro: lógica de patrulha/diálogo
        pass
