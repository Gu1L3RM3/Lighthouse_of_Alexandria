from core.ecs import Component
from entities.firearm import FireArm

class WeaponSlot(Component):
    #TODO: criar uma classe abc para armas
    def __init__(self,weapon:FireArm=None):
        self.weapon=weapon
        