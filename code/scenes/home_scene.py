from pygame import Surface
from scenes.base_scene import BaseScene
from core.config import *
class HomeScene(BaseScene):
    def __init__(self,screen: Surface):
        super().__init__(screen)
        
        self.font = self.resources.load_font("PressStart2P-Regular.ttf", 48)

        self.text = "Home Page"

        self.text_surf = self.font.render(self.text, True, (255, 255, 255))

        self.text_rect = self.text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    def process_input(self, events):
        pass

    def update(self, dt: float) -> None:
        pass
    def render(self) -> None:
        self.screen.fill((0,100,0))
        self.screen.blit(self.text_surf,self.text_rect)
    