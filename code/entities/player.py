from core.components.position import Position
from core.components.velocity import Velocity
from core.components.sprite import Sprite
from core.components.collider import Collider
from core.settings import *
from core.ecs import Entity
from entities.firearm import FireArm
from core.components.weapon_slot import WeaponSlot
from pygame import Vector2,Event,Surface

from pygame.key import get_pressed
class Player(Entity):
    def __init__(self,x:float=100,y:float=100):
        super().__init__()
        self.is_collided=False
        self._direction=Vector2(0,0)
        self._old_direction=Vector2(0,1)
        self._key_to_direction = {
            PLAYER_RIGHT: Vector2(1, 0),
            PLAYER_LEFT: Vector2(-1, 0),
            PLAYER_DOWN: Vector2(0, 1),
            PLAYER_UP: Vector2(0, -1),
        }
        self._speed=200

        pos=Position(x,y)
        vel=Velocity(0,0)
        col=Collider(16,16)

        image=Surface((16,16))
        image.fill(WHITE)
        spr=Sprite(image)

        weapon=FireArm(Position(x+8,y+8))
        weapon_slot=WeaponSlot(weapon)

        self.add(pos,vel,spr,col,weapon_slot)
    @property
    def old_direction(self):
        return self._old_direction
    def get_weapon(self):
        weapon_slot:WeaponSlot=self.get(WeaponSlot)
        return weapon_slot.weapon
    
    def input(self, events:list[Event]):
        self._direction.update(0,0)

        vel :Velocity= self.get(Velocity)
        if self.is_collided:
            self._direction.update(0,0)
            vel.vxy=(0,0)
            return 
        
        keys= get_pressed()
        
        for key,vector in self._key_to_direction.items():
            if keys[key]:
                self._direction+=vector
                self._old_direction=self._direction



            
        if self._direction.length_squared()>0:
            self._direction=self._direction.normalize()

        vel.vxy=(self._direction.x*self._speed,
                 self._direction.y*self._speed)
            

        

        