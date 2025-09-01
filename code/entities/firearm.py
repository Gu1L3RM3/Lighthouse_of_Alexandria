from core.ecs import Entity
from core.components.sprite import Sprite
from pygame import Surface


class FireArm(Entity):
    def __init__(self):
        super().__init__()
        image=Surface((16,8))
        image.fill((50,200,50))
        spr=Sprite(image)
        self.add(spr)
        

    