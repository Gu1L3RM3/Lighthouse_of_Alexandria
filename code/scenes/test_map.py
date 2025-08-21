from pygame import Surface
from scenes.base_scene import BaseScene
from entities.player import Player
from systems.map_system import MapSystem
from systems.physics_system import PhysicsSystem
from systems.dialogue_system import DialogueSystem
from systems.npc_route_system import NPCRouteSystem
from systems.path_following_system import PathFollowingSystem
from core.day_night_manager import DayNightManager
from ui.widgets.hud import HUD
from ui.ui_manager import UIManager

class TestMap(BaseScene):
    def __init__(self, screen: Surface):
        self.map = MapSystem("teste.tmx")  
        
        super().__init__(screen, self.map.map_width, self.map.map_height)

        self.dn_manager = DayNightManager(screen)
        self.ui_manager = UIManager()

        self.hud=HUD(screen,self.dn_manager)
        self.ui_manager.add(self.hud)

        self.entities = []
        self.set_map()
        self.camera.follow = self.player
        self.show_nav_overlay = True

        self.physics_system = PhysicsSystem()
        self.dialog_system = DialogueSystem(self.ui_manager)
        self.npc_route_system = NPCRouteSystem(self.map, self.dn_manager)
        self.path_following_system = PathFollowingSystem(self.map.navgrid)

    def set_map(self):
        self.map.load_map(self.entities)
        px, py = self.map.get_player_spawn()
        self.player = Player(px, py)
        self.entities.append(self.player)

    def process_input(self, events):
        # trava input do player enquanto há diálogo
        if not self.dialog_system.active_dialogue_npc:
            self.player.input(events)

    def update(self, dt):
        # diálogos primeiro (podem congelar NPCs via Freeze se você ligar o evento)
        self.dialog_system.update(self.entities, self.player,dt)

        if not self.dialog_system.active_dialogue_npc:
            self.dn_manager.update(dt)
            # rotina de NPC → cria/atualiza seguidores de caminho
            self.npc_route_system.update(self.entities)

            # segue caminho (move NPCs somente em ground2)
            self.path_following_system.update(self.entities, dt)

        self.ui_manager.update(dt)

        self.physics_system.update(self.entities, dt)
        self.render_system.update(dt)
    def render(self):
        self.screen.fill((0,0,50))

        self.render_system.draw(self.entities)
        
        self.ui_manager.draw(self.screen)
        self.dn_manager.draw()

        
