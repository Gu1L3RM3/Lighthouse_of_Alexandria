from pygame import Surface
from core.settings import *
from scenes.base_scene import BaseScene
from entities.player import Player
from core.systems.enemies_follow_system import EnemiesFollowSystem
from core.ui.widgets.fps_widget import FPSWidget
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.map.map_entity_spawner import MapEntitySpawner
class PuzzleMap(BaseScene):
    def __init__(self, screen:Surface):
        loader = TileMapLoader()
        self.tile_map=loader.load("puzzle_test.tmx")
        super().__init__(screen, self.tile_map.map_width, self.tile_map.map_height)

        self.enemies_follow_system=EnemiesFollowSystem(self.tile_map)
        
        self.map_renderer=MapRenderer(self.tile_map,self.camera,self.screen)

        fps=FPSWidget()
        self.ui_manager.add(fps)
        self.set_map()


        
        
        self.camera.follow = self.player

        self.systems.update(
            [self.physics_system,
            self.enemies_follow_system,
            self.path_following_system,
            self.weapon_system,
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

        if not self.dialog_system.active_dialogue_npc:
            self.player.input(events)

    def update(self, dt):

        self.update_systems(dt)
        self.ui_manager.update(dt)
       
    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw() 
        self.ui_manager.draw(self.screen)
        self.dn_manager.draw()