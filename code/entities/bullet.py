from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
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
        
        col = Collider(4, 4)

        self.life_time = life_time  
        self.age = 0

        self.add(pos, vel, spr)

    def update_age(self, dt):
        self.age += dt
        return self.age < self.life_time
