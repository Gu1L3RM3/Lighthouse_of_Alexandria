from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.ecs import Entity
from pygame import Vector2,Event,Surface
from pygame.locals import *
from pygame.key import get_pressed
class Player(Entity):
    def __init__(self,x:float=100,y:float=100):
        super().__init__()
        self.__direction=Vector2(0,0)
        self.__key_to_direction = {
            K_RIGHT: Vector2(1, 0),
            K_LEFT: Vector2(-1, 0),
            K_DOWN: Vector2(0, 1),
            K_UP: Vector2(0, -1),
        }
        self.__speed=200

        pos=Position(x,y)
        vel=Velocity(0,0)

        image=Surface((32,32))
        image.fill((255,0,0))

        spr=Sprite(image)
        self.add(pos,vel,spr)

    
    def input(self, events:list[Event]):
        self.__direction.update(0,0)

        vel :Velocity= self.get(Velocity)
        keys= get_pressed()
        #0(n)
        for key,vector in self.__key_to_direction.items():
            if keys[key]:
                self.__direction+=vector



            
        if self.__direction.length_squared()>0:
            self.__direction=self.__direction.normalize()

        vel.vxy=(self.__direction.x*self.__speed,
                 self.__direction.y*self.__speed)
            

        

        