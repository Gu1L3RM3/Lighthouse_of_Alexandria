from pygame import Surface
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.dialogue import Dialogue
from core.settings import *
class GuardNPC(Entity):
    def __init__(self, x, y, props=None):
       super().__init__()
       image=Surface((16,16))
       image.fill(GREEN)


     
       self.add(Position(x,y),
                Collider(16,16),
                Sprite(image),
                Dialogue(["Tenho que estudar para a prova de amanhã"]),
                Velocity(),
                Freeze()
                )
       self.props = props or {}
    
    def update(self, dt):
        # Futuro: lógica de patrulha/diálogo
        pass
