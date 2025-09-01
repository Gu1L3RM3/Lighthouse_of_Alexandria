from core.ecs import Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.settings import *
from pygame import Surface, Vector2

class Bullet(Entity):
    def __init__(self, x: float, y: float, direction: Vector2, speed: float = 400):
        super().__init__()

        pos = Position(x, y)
        vel = Velocity(direction.x * speed, direction.y * speed)

        image = Surface((4, 4))
        image.fill(YELLOW)
        spr = Sprite(image)

        col = Collider(4,4)

        self.add(pos, vel, spr, col)
