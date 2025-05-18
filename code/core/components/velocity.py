from core.ecs import Component
from pygame import Vector2
from typing import Tuple
class Velocity(Component):
    def __init__(self, vx: float = 0, vy: float = 0):
        self._vel=Vector2(vx,vy)
    @property
    def vel(self)->Vector2:
        return self._vel
    @vel.setter
    def vel(self,value:Vector2):
        self._vel=value
    @property
    def vx(self)->float:
        return self.vel.x
    @vx.setter
    def vx(self,value:float):
        self.vel.x=value
    @property
    def vy(self)->float:
        return self.vel.y
    @vy.setter
    def vy(self,value:float):
        self.vel.y=value
    @property    
    def vxy(self)->Vector2:
        return self._vel.xy
    @vxy.setter
    def vxy(self,value:Tuple[float,float]):
        self._vel.xy=value
    