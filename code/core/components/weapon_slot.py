from core.ecs import Component
from entities.weapons.weapon import Weapon

class WeaponSlot(Component):
    def __init__(self,weapon:Weapon|None):
        self.weapon=weapon
    def to_dict(self):
        pass
        