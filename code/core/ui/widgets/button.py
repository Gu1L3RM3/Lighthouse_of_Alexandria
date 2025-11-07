from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import *
from core.ui.widgets.text import Text
from typing import Callable

class Button(Widget):
    def __init__(self,
                 init_surface: Surface,
                 surface_pressed: Surface,
                 pos_center: tuple[int, int],
                 click_type:ClickType|None=None,
                 action: Callable|None=None,
                 gesture_detector:GestureDetector|None=None,
                 text:str|None=None,
                 font_size:int|None=None,
                 text_widget: Text | None = None,
                 draw_gesture_detector: bool = False,
                 color:tuple[int,int,int]|None=None,
                 color_text:tuple[int,int,int]=(255,255,255),
                 font:str="PressStart2P-Regular.ttf"):
        if color!=None:
            init_surface.fill(color)

        self.action = action
        self.click_type = click_type
        self.surface_pressed = surface_pressed
        self.init_surface = init_surface
        self.current_surf = self.init_surface
        self.pos_center = pos_center
        self._rect = self.current_surf.get_rect(center=self.pos_center)
        self.draw_gesture_detector = draw_gesture_detector
        self.gesture_detector = gesture_detector
        self.set_gesture_detector()
        self.text_widget = text_widget
        self.text = text
        self.font_size = font_size
        self.color_text = color_text
        self.font = font
        self.set_text()

    def set_gesture_detector(self):
        if self.gesture_detector == None:
            self.gesture_detector = GestureDetector(
                size=self.init_surface.get_size(),
                function=self.action,
                click_type=self.click_type,
            )
    def change_text(self,text:str):
        self.text_widget.set_text(text,self._rect.center)
    def set_text(self):
        if self.text_widget == None:
            self.text_widget = Text(
                text=self.text,
                font_size=self.font_size,
                font_color=self.color_text,
                pos_center=self._rect.center,
                font_name=self.font
            )

    def update(self, dt):
        self.gesture_detector.update(dt)
        pressed = self.gesture_detector._hold_state if self.click_type == ClickType.HOLD else self.gesture_detector.is_pressed
        self.current_surf = self.surface_pressed if pressed else self.init_surface
        self._rect = self.current_surf.get_rect(center=self.pos_center)
        self.gesture_detector.rect.center = self._rect.center
        if self.text_widget:
            self.text_widget.rect.center = self._rect.center

    def draw(self, surface):
        surface.blit(self.current_surf, self._rect)
        if self.text_widget:
            self.text_widget.draw(surface)
        if self.draw_gesture_detector:
            self.gesture_detector.draw(surface)