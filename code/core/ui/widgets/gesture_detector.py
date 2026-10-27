import pygame
from pygame import Surface, Rect
from core.ui.widgets.widget import Widget
from enum import Enum
from typing import Callable
from core.touch_points import TouchPoints

class ClickType(Enum):
    AFTER_RELEASED = 0
    AFTER_PRESSED  = 1
    HOLD  = 2

class GestureDetector(Widget):
    def __init__(self, 
                 size: tuple[int, int],
                 function: Callable,
                 click_type: ClickType = ClickType.AFTER_RELEASED,
                 show_debug_surf: bool = False,
                 offset: tuple[int,int] = (0,0),
                 touch_points: TouchPoints | None = None,
                 accepts_touch: bool = True):
        self.click_type = click_type
        # The circuit grid opts out: the editor places parts when the finger lifts, not here.
        self.accepts_touch = accepts_touch
        self.touch_points = touch_points or TouchPoints.get()
        self.function = function
        self.show_debug_surf = show_debug_surf
        self.rect = Rect((0+offset[0], 0+offset[1]), size)
        self.is_pressed = False
        self.is_hovered = False
        self._was_pressed_last_frame = False
        self._hold_state = False
        self.debug_surf = Surface(self.rect.size, pygame.SRCALPHA)
        self.debug_surf.fill((0, 255, 0, 100))

    def update(self, dt):
        touched = self.accepts_touch and any(self.rect.collidepoint(pos) for pos in self.touch_points.pressed_positions())
        lifted = self.accepts_touch and any(self.rect.collidepoint(pos) for pos in self.touch_points.released_positions())
        if self.touch_points.touched_recently():
            # the mouse state here is the browser's emulated click for the same tap
            self.is_hovered = touched or lifted
            self.is_pressed = touched
        else:
            mouse_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
            self.is_hovered = mouse_hovered or touched or lifted
            self.is_pressed = touched or (mouse_hovered and pygame.mouse.get_pressed()[0])

        self._pressed()
        self._release()
        self._hold_once()

        self._was_pressed_last_frame = self.is_pressed

    def _pressed(self):
        if self.click_type != ClickType.AFTER_PRESSED:
            return
        if self.is_pressed and not self._was_pressed_last_frame:
            self.function()

    def _hold_once(self):
        if self.click_type != ClickType.HOLD:
            return
        if self.is_pressed and not self._was_pressed_last_frame:
            self._hold_state = not self._hold_state
            try:
                self.function(self._hold_state)
            except : raise Exception("Fuction must has a bool parameter")

    def _release(self):
        if self.click_type != ClickType.AFTER_RELEASED:
            return
        if not self.is_pressed and self._was_pressed_last_frame and self.is_hovered:
            self.function()

    def draw(self, surface):
        if self.show_debug_surf:
            surface.blit(self.debug_surf, self.rect)