import pygame
from pygame import Surface, Rect
from core.ui.widgets.widget import Widget
from enum import Enum
from typing import Callable

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
                 offset: tuple[int,int] = (0,0)):
        self.click_type = click_type
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
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        left_button_pressed = mouse_buttons[0]

        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.is_pressed = self.is_hovered and left_button_pressed

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