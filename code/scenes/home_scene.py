from pygame import Surface
from scenes.base_scene import BaseScene
from core.config import *
from pygame.locals import *
from ui.widgets.type_writer import TypewriterEffect
from core.scene_manager import SceneManager
from ui.ui_manager import UIManager
class HomeScene(BaseScene):
    def __init__(self,screen: Surface):
        screen_w=screen.get_width()
        screen_h=screen.get_height()
        super().__init__(screen,screen_w,screen_h)

        self.type_writer=TypewriterEffect(
            position=(screen_w//2, screen_h//2),
            font_color=(255,255,255),
            font_size=20,
            font_name="PressStart2P-Regular.ttf",
            text="Home Page!!"
        )
        self.ui_manager=UIManager()
        self.ui_manager.add(self.type_writer)
        self.scene_manager=SceneManager.get()
        
        

    def process_input(self, events):
        for event in events:
            if event.type == KEYDOWN and event.key == K_SPACE:
                self.scene_manager.start_fade("teste",duration=1.0)

    def update(self, dt: float) -> None:
        self.ui_manager.update(dt)
        self.scene_manager.update_transition()
    def render(self) -> None:
        self.screen.fill((0,100,0))
        self.ui_manager.draw(self.screen)
        self.scene_manager.draw_transition(self.screen)