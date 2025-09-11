from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.managers.time_manager import TimeManager
from core.ecs import Entity
from pygame import Surface, Vector2
from core.settings import YELLOW

class Bullet(Entity):
    def __init__(self, pos: Position, direction: Vector2, speed: float = 400, life_time: float = 2.0):
        super().__init__()
        vel = Velocity(direction.x * speed, direction.y * speed)
        
        image = Surface((4, 4))
        image.fill(YELLOW)
        spr = Sprite(image)
        

        self.life_time = life_time  
        self.timer=TimeManager()
        self.timer.set("life", life_time)

        self.add(pos,
                 vel,
                 spr,
                 
                 )

    def is_alive(self):
        return not self.timer.ready("life")
    
