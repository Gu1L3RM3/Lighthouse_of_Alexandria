from pygame import Surface
from scenes.base_scene import BaseScene
from core.components.sprite import Sprite
from core.components.position import Position
from entities.player import Player
from core.ecs import Entity
class TestScene(BaseScene):
    def __init__(self,screen:Surface):
        super().__init__(screen,3000,2000)
        self.player= Player()
        img=Surface((30,30))
        self.e = Entity()
        self.e.add(Position(500, 500),Sprite(img))
       
        self.entities=[self.player,self.e]
        self.camera.follow=self.player
        

    def process_input(self, events):
        self.player.input(events)

    def update(self, dt):
        self.movement_system.update(self.entities,dt)
    

    def render(self):
        self.screen.fill((0, 0, 50))
        self.render_system.update(self.entities)
