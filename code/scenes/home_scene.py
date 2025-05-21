from pygame import Surface
from scenes.base_scene import BaseScene
from core.config import *
from pygame.locals import *
from core.scene_manager import SceneManager
class HomeScene(BaseScene):
    def __init__(self,screen: Surface):
        screen_w=screen.get_width()
        screen_h=screen.get_height()
        super().__init__(screen,screen_w,screen_h)
        
        self.font = self.resources.load_font("PressStart2P-Regular.ttf", 48)

        self.text = "Home Page"

        self.text_surf = self.font.render(self.text, True, (255, 255, 255))

        self.text_rect = self.text_surf.get_rect(center=(screen_w//2, screen_h//2))
    def process_input(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_SPACE:
                SceneManager.get().change("teste")

    def update(self, dt: float) -> None:
        pass
    def render(self) -> None:
        self.screen.fill((0,100,0))
        self.screen.blit(self.text_surf,self.text_rect)
    