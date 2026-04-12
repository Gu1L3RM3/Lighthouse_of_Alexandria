import pygame
from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import *
from core.ui.widgets.text import Text
from typing import Callable
from core.managers.audio_manager import AudioManager

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
        self.audio = AudioManager.get()
        self._was_hovered_last_frame = False
        self._was_pressed_last_frame = False
        self._pressed_feedback_timer = 0.0
        self._suppress_next_press_sound = False
        self._is_focused = False
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

    def set_focused(self, focused: bool):
        self._is_focused = focused

    def activate(self, press_feedback_seconds: float = 0.14, trigger_action: bool = True):
        self._pressed_feedback_timer = max(self._pressed_feedback_timer, max(0.0, press_feedback_seconds))
        self._suppress_next_press_sound = True
        self.audio.play_ui("sfx/ui_click.wav", volume=0.9)
        if trigger_action and self.action:
            self.action()

    def update(self, dt):
        self.gesture_detector.update(dt)
        if self._pressed_feedback_timer > 0:
            self._pressed_feedback_timer = max(0.0, self._pressed_feedback_timer - dt)
        gesture_pressed = self.gesture_detector._hold_state if self.click_type == ClickType.HOLD else self.gesture_detector.is_pressed
        pressed = gesture_pressed or self._pressed_feedback_timer > 0
        if self.gesture_detector.is_hovered and not self._was_hovered_last_frame:
            self.audio.play_ui("sfx/ui_hover.wav", volume=0.75)
        if pressed and not self._was_pressed_last_frame:
            if self._suppress_next_press_sound:
                self._suppress_next_press_sound = False
            else:
                self.audio.play_ui("sfx/ui_click.wav", volume=0.9)
        if not pressed:
            self._suppress_next_press_sound = False
        self._was_hovered_last_frame = self.gesture_detector.is_hovered
        self._was_pressed_last_frame = pressed
        self.current_surf = self.surface_pressed if pressed else self.init_surface
        self._rect = self.current_surf.get_rect(center=self.pos_center)
        self.gesture_detector.rect.center = self._rect.center
        if self.text_widget:
            self.text_widget.rect.center = self._rect.center

    def draw(self, surface):
        surface.blit(self.current_surf, self._rect)
        if self._is_focused:
            pygame.draw.rect(surface, (245, 230, 170), self._rect.inflate(8, 8), 3, border_radius=6)
        if self.text_widget:
            self.text_widget.draw(surface)
        if self.draw_gesture_detector:
            self.gesture_detector.draw(surface)
