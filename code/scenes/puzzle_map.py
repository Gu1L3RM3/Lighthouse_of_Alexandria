from pygame import Surface
from core.settings import *
from scenes.base_scene import BaseScene
from entities.player import Player
from systems.map_system import MapSystem
from systems.physics_system import PhysicsSystem
from systems.dialogue_system import DialogueSystem
from systems.npc_route_system import NPCRouteSystem
from systems.path_following_system import PathFollowingSystem
from systems.weapon_system import WeaponSystem
from systems.render_system import RenderSystem
from systems.enemies_follow_system import EnemiesFollowSystem
from core.managers.day_night_manager import DayNightManager
from ui.widgets.hud import HUD
from ui.ui_manager import UIManager
from core.managers.entity_manager import EntityManager

class PuzzleMap(BaseScene):
    def __init__(self, screen:Surface):
        self.map = MapSystem("puzzle_test.tmx") 
        super().__init__(screen, self.map.map_width, self.map.map_height)
        self.dn_manager = DayNightManager(screen)
        self.ui_manager = UIManager()

        self.physics_system = PhysicsSystem()
        
        self.dialog_system = DialogueSystem(self.ui_manager)
        self.path_following_system = PathFollowingSystem()

        self.entity_mn=EntityManager()
        self.set_map()
        self.render_system=RenderSystem(self.screen,self.camera,self.entity_mn,self.map)
        self.enemies_follow_system=EnemiesFollowSystem(self.map)
        self.weapon_system=WeaponSystem()

        self.hud=HUD(screen,self.dn_manager)
        self.ui_manager.add(self.hud)


        
        
        self.camera.follow = self.player
        self.show_nav_overlay = True

    def set_map(self):
        self.map.load_map(self.entity_mn)
        px, py = self.map.get_player_spawn()
        self.player = Player(px, py)
        self.entity_mn.add_entity(self.player)
        self.physics_system.cache_static_colliders(self.entity_mn)
    def process_input(self, events):

        if not self.dialog_system.active_dialogue_npc:
            self.player.input(events)

    def update(self, dt):
    

        self.dialog_system.update(self.entity_mn, self.player,dt)

        if self.dialog_system.active_dialogue_npc:
            return

        self.physics_system.update(self.entity_mn, dt)
        self.dn_manager.update(dt)

        self.enemies_follow_system.update(self.entity_mn,dt)
        self.path_following_system.update(self.entity_mn, dt)
        

        self.ui_manager.update(dt)
        self.weapon_system.update(self.entity_mn,dt)
        self.render_system.update(dt)
    def render(self):
        self.screen.fill(BLACK)
        self.render_system.draw() 
        self.ui_manager.draw(self.screen)
        self.dn_manager.draw()