from core.ecs import Component
from pygame import Vector2
from typing import Tuple
class Position(Component):
    def __init__(self,x: float =0,y:float =0):
        self._pos=Vector2(x,y)
    @property
    def pos(self)->Vector2:
        return self._pos
    @pos.setter
    def pos(self,value:Vector2):
        self._pos=value
    @property
    def x(self) -> float:
        return self._pos.x

    @x.setter
    def x(self, value: float):
        self._pos.x = value

    @property
    def y(self) -> float:
        return self._pos.y

    @y.setter
    def y(self, value: float):
        self._pos.y = value
    @property
    def xy(self) -> Tuple[float, float]:
        
        return self._pos.xy

    @xy.setter
    def xy(self, value: Tuple[float, float]):
        self._pos.xy=value