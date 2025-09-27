import pygame
from core.settings import *
from pygame import Surface
from scenes.base_scene import BaseScene
from entities.player import Player
from core.systems.npc_route_system import NPCRouteSystem
from core.systems.animation_system import AnimationSystem
from core.ui.widgets.hud import HUD
from core.managers.scene_manager import SceneManager
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.map.map_entity_spawner import MapEntitySpawner

class TestMap(BaseScene):
    def __init__(self, screen: Surface):
        loader = TileMapLoader()
        self.tile_map = loader.load("teste.tmx")

        super().__init__(screen, self.tile_map.map_width, self.tile_map.map_height)

        self.map_renderer = MapRenderer(self.tile_map, self.camera, self.screen)

        self.hud = HUD(self.dn_manager)
        self.ui_manager.add(self.hud)

        self.npc_route_system = NPCRouteSystem(self.tile_map, self.dn_manager)
        self.animation_system =  AnimationSystem()

        
        self.set_map()

        self.camera.follow = self.player
        
        self.systems.update(
            [self.physics_system,
            self.npc_route_system,
            self.path_following_system,
            self.animation_system,
            self.render_system]
            )

    def set_map(self):
        spawner = MapEntitySpawner()
        
        spawner.spawn_entities(self.tile_map, self.entity_mn)
        px, py = self.tile_map.get_player_spawn()

        self.player = Player(px, py)

        self.entity_mn.add_entity(self.player)
        self.physics_system.cache_static_colliders(self.entity_mn)

    def process_input(self, events):
        if self.dialog_system.active_dialogue_npc:
            return

        if self.time_manager.ready("next_scene"):
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == KEY_NEXT_SCENE:
                    SceneManager.get().start_fade('puzzle', 0.25)
                    self.time_manager.set("next_scene",0.25)  

                

        
        self.player.input(events)

    def update(self, dt):
        
        
        self.dialog_system.update(self.entity_mn, self.player,dt)

        if self.dialog_system.active_dialogue_npc:
            return

        self.dn_manager.update(dt)
        self.update_systems(dt)


        self.ui_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 50))
        self.map_renderer.draw()
        self.render_system.draw() 
        self.dn_manager.draw()
        self.ui_manager.draw(self.screen)


        
