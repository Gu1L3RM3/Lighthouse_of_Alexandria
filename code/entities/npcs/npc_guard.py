from pygame import Surface
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.dialogue import Dialogue
from core.settings import *
from core.managers.resource_manager import ResourceManager
class GuardNPC(Entity):
    def __init__(self, x, y, props=None):
       super().__init__()
       self.rm=ResourceManager.get()
       sprites=self.rm.load_sprite_sheet('player')

       image=sprites['idle_front'][0]


     
       self.add(Position(x,y),
                Collider(10, 6,offset_x=2,offset_y=13),
                Sprite(image),
                Dialogue(["Tenho que estudar para a prova de amanhã"]),
                Velocity(),
                Freeze()
                )
       self.props = props or {}
    
    
