from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from pygame import Surface


class Delete(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf = Surface((64,64))
        surf.fill((200,50,50))

        self.add(
            Sprite(surf),
            Position(x,y)
        )

class Rotate(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf = Surface((64,64))
        surf.fill((200, 120, 50))

        self.add(
            Sprite(surf),
            Position(x,y)
        )


class Rotate(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf = Surface((64,64))
        surf.fill((200, 120, 50))

        self.add(
            Sprite(surf),
            Position(x,y)
        )

class Select(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf = Surface((64,64))
        surf.fill((200, 150, 150))

        self.add(
            Sprite(surf),
            Position(x,y)
        )
