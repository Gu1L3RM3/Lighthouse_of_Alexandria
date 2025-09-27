from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from pygame import Surface

class Resistor(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((32*4,64))
        surf.fill((200,170,10))
        self.add(
            Position(x,y),
            Sprite(surf),
            Dropped(),
           
        )


        

class VoutageSource(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((32*4,64))
        surf.fill((0,100,188))
        self.add(
            Position(x,y),
            Sprite(surf),
            Dropped(),
           
        )

class CurrentSource(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((32*4,64))
        surf.fill((20,100,10))
        self.add(
            Position(x,y),
            Sprite(surf),
            Dropped(),
           
        )

class Ground(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((64,64))
        surf.fill((100,150,200))
        self.add(
            Position(x,y),
            Sprite(surf),
            Dropped(),
           
        )
class Wire(Entity):
    def __init__(self,x,y):
        super().__init__()
        surf=Surface((32*4,64))
        surf.fill((30,60,70))
        self.add(
            Position(x,y),
            Sprite(surf),
            Dropped(),
           
        )