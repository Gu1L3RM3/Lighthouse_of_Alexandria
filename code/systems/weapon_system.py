import pygame
from pygame.math import Vector2
from core.settings import *
from core.ecs import System
from core.components.position import Position
from core.managers.entity_manager import EntityManager
from entities.bullet import Bullet
from entities.player import Player


class WeaponSystem(System):
    def __init__(self):
        super().__init__()
        self.time_since_last_shot=0
        self.fire_rate=0.2
    def update(self, entity_mn: EntityManager, dt):

        self.time_since_last_shot += dt
        player: Player = entity_mn.get_player()
        #self._set_weapon(player, entity_mn)
        self._handle_input(player, entity_mn, dt)
        self._kill_bullets(entity_mn,dt)

    
    def _handle_input(self, player: Player, entity_mn: EntityManager, dt):
        keys = pygame.key.get_pressed()
        if not keys[PLAYER_SHOOT]:
            return
        
        if self.time_since_last_shot < self.fire_rate:
            return

        self.time_since_last_shot = 0
        
        player_pos: Position = player.get(Position)
        dir_vec = player.old_direction
        spawn_offset = Vector2(0,0)

        if dir_vec == Vector2(1,0):
            spawn_offset = Vector2(16,8)  
        elif dir_vec == Vector2(-1,0):
            spawn_offset = Vector2(-16,8)  
        elif dir_vec == Vector2(0,1):
            spawn_offset = Vector2(8,16)  
        elif dir_vec == Vector2(0,-1):
            spawn_offset = Vector2(8,-16)  

        init_pos = Position(player_pos.x + spawn_offset.x, player_pos.y + spawn_offset.y)
        bullet = Bullet(init_pos, dir_vec)
        entity_mn.add_entity(bullet)

    
    def _kill_bullets(self,entity_mn:EntityManager,dt):
        for entity in entity_mn.get_entities():
            if not isinstance(entity, Bullet):
                continue
            if not entity.update_age(dt): 
                entity_mn.remove_entity(entity)

  

   
    def _set_weapon(self, player: Player, entity_mn: EntityManager):
        weapon = player.get_weapon()
        if weapon.id not in entity_mn.entities:
            entity_mn.add_entity(weapon)

        weapon_pos: Position = weapon.get(Position)
        player_pos: Position = player.get(Position)
        dir_vec = player.old_direction

        if dir_vec == Vector2(1, 0):      
            weapon_offset = Vector2(16, 8)
        elif dir_vec == Vector2(-1, 0):    
            weapon_offset = Vector2(-16, 8)
        elif dir_vec == Vector2(0, 1):     
            weapon_offset = Vector2(8, 16)
        elif dir_vec == Vector2(0, -1):   
            weapon_offset = Vector2(8, -16)
        else:                             
            weapon_offset = Vector2(8, 8)

       
        weapon_pos.x = player_pos.x + weapon_offset.x
        weapon_pos.y = player_pos.y + weapon_offset.y
        

        
    
        
    

