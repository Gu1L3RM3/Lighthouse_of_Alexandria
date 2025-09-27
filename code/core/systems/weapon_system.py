import pygame
from core.settings import *
from core.ecs import System
from core.components.weapon_slot import WeaponSlot
from core.managers.entity_manager import EntityManager
from core.managers.time_manager import TimeManager
from entities.player import Player
from entities.weapons.weapon import Weapon
from core.components.position import Position

class WeaponSystem(System):
    def __init__(self):
        super().__init__()
        self.attack_rate = 0.1 
        self.timer = TimeManager()
        self.timer_name = "attack"
        self.timer.set(self.timer_name, self.attack_rate)

    def update(self, entity_mn: EntityManager, dt: float):
        self._handle_input(entity_mn)

    def _handle_input(self, entity_mn: EntityManager):
        player: Player = entity_mn.get_player()
        if not player or not player.has(WeaponSlot):
            return

        weapon_slot: WeaponSlot = player.get(WeaponSlot)
        weapon: Weapon = weapon_slot.weapon
        if not weapon:
            return

        keys = pygame.key.get_pressed()
        if not keys[PLAYER_ATTACK]:
            return

        if not self.timer.ready(self.timer_name):
            return

        self.timer.set(self.timer_name, self.attack_rate)
        pos: Position = player.get(Position)
        weapon.attack(pos, player.old_direction, entity_mn)
