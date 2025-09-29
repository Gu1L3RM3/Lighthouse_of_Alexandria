from core.ecs import Component
from pygame import Vector2
from typing import Tuple
from core.settings import *
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

    def center_pos(self)->Vector2:
        return Vector2(
            self._pos.x+(TILE_SIZE//2),
            self._pos.y+(TILE_SIZE//2)
        )
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'x':self.x,
            'y':self.y

        }
    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
            
        x = data['x']
        y = data['y']
        
        return cls(x,y)