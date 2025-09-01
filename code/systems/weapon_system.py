import pygame
from pygame.math import Vector2
from core.settings import *
from core.ecs import System
from core.components.position import Position
from core.components.weapon_slot import WeaponSlot
from core.managers.entity_manager import EntityManager
from entities.bullet import Bullet

class WeaponSystem(System):
    def _handle_input(self,pos:Position,entity_mn:EntityManager,dt):
        key=pygame.key.get_just_pressed()
        if key[PLAYER_SHOOT]:
            bullet = Bullet(pos.x + 16, pos.y + 8, Vector2(1, 0))
            entity_mn.add_entity(bullet)
    def update(self, entity_mn:EntityManager, dt):
        entities_has_weapon=entity_mn.get_entities_with(Position,WeaponSlot)
        for e in entities_has_weapon:
            
            pos:Position = e.get(Position)
            slot:WeaponSlot = e.get(WeaponSlot)

            if not slot.weapon:
                return
            
            weapon_pos :Position= slot.weapon.get(Position)

            if not weapon_pos :
                return
                
            weapon_pos.x=pos.x+10
            weapon_pos.y=pos.y+5

            self._handle_input(pos,entity_mn,dt)

