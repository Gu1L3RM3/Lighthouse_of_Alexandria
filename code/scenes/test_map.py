from pygame import Surface
from scenes.base_scene import BaseScene
from entities.player import Player
from systems.map_system import MapSystem
from systems.physics_system import PhysicsSystem
from systems.dialogue_system import DialogueSystem
from core.day_night_manager import DayNightManager
class TestMap(BaseScene):
    def __init__(self,screen:Surface):
        self.map=MapSystem("teste.tmx")
        self.physics_system=PhysicsSystem()
        super().__init__(screen,self.map.map_width,self.map.map_height)

        self.dn_manager=DayNightManager(screen,0.2)

        self.entities=[]
        self.set_map()
        self.camera.follow=self.player

        self.dialog_system=DialogueSystem()
    
    def set_map(self):
        self.map.load_map(self.entities)

        player_spawn=self.map.get_player_spawn()
        x,y=player_spawn
        self.player=Player(x,y)
        self.entities.append(self.player)
    

        

    def process_input(self, events):
        if not self.dialog_system.active_dialogue:
            self.player.input(events)

    def update(self, dt):
        self.dialog_system.update(self.entities,self.player)
        self.physics_system.update(self.entities,dt)
        self.dn_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 50))
        self.render_system.update(self.entities)
        self.dialog_system.draw(self.screen)
        self.dn_manager.draw()