from __future__ import annotations  


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.managers.entity_manager import EntityManager

from core.components.position import Position
from pygame import Vector2
class Weapon(ABC):
    @abstractmethod
    def attack(self,position:Position,old_direction:Vector2,entity_mn:EntityManager):
        pass

