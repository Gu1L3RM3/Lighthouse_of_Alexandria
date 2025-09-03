from pygame import Surface
from core.ecs import Entity
from core.settings import *
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.player_follower import PlayerFollower
class Enemie(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((TILE_SIZE,TILE_SIZE))
        surf.fill(RED)

        

        self.add(
            Position(x,y),
            #Collider(10,10),
            Sprite(surf),
            Velocity(),
            PlayerFollower(0.1,40)
        )

        

