from pygame import Surface
from scenes.base_scene import BaseScene
from core.settings import *
from pygame.locals import *
from core.ui.widgets.type_writer import TypewriterEffect
from core.managers.scene_manager import SceneManager
from core.managers.ui_manager import UIManager
from core.managers.resource_manager import ResourceManager
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import *
from core.ui.widgets.text import Text

class HomeScene(BaseScene):
    def __init__(self,screen: Surface):
        screen_w=screen.get_width()
        screen_h=screen.get_height()
        super().__init__(screen,screen_w,screen_h)
        self.rm=ResourceManager.get()
        

        self.type_writer=TypewriterEffect(
            position=(screen_w//2, 60),
            font_color=WHITE,
            font_size=80,
            font_name=FONT,
            text="Menu"
        )
        
        size_button=(100,100)
        surf=self.rm.load_image('buttons/play.png',size=size_button)
        surf_1=self.rm.load_image('buttons/play_pressed.png',size=size_button)
        

        self.button_play=Button(
            init_surface=surf,
            surface_pressed=surf_1,
            pos_center=(screen_w//2, screen_h//2),
            draw_gesture_detector=True,
            gesture_detector=GestureDetector(
                click_type=ClickType.AFTER_RELEASED,
                function=self._action_button,
                # TODO:fazer enum para size
                size= surf.get_size(),)

        )
        

        self.ui_manager=UIManager()
        self.ui_manager.add(self.type_writer,self.button_play)
        self.scene_manager=SceneManager.get()
        
        
    def _action_button(self):
        self.scene_manager.start_fade("teste",duration=0.5)
    def process_input(self, events):
        pass

    def update(self, dt: float) -> None:
        self.ui_manager.update(dt)
        self.scene_manager.update_transition()
    def render(self) -> None:
        self.screen.fill((0,0,0))
        self.ui_manager.draw(self.screen)
        self.scene_manager.draw_transition(self.screen)