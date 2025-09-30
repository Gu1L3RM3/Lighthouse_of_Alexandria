import pygame
from pygame import Surface, Rect
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import  ClickType
from core.ui.widgets.button import Button
from core.managers.resource_manager import ResourceManager
from typing import Callable, Optional


class EletricList(Widget):
    '''list_type can be Resistor ,
       VoutageSource , CurrenteSource'''
    def __init__(self,
                 data: dict,                 
                 list_type: str,             
                 screen_size: tuple[int, int],
                 button_size: tuple[int, int] = (200, 50),
                 spacing: int = 10,
                 action: Optional[Callable] = None,
                 on_close: Optional[Callable] = None):
        super().__init__()
        self.data = data
        self.list_type = list_type
        self.button_size = (int(button_size[0]), int(button_size[1]))
        self.spacing = int(spacing)
        self.action = action
        self.on_close = on_close
        self.buttons: list[Button] = []
        self.rm = ResourceManager.get()

        num_items = len(self.data.get(self.list_type, {}))

        dialog_width = self.button_size[0] + 80
        dialog_height = num_items * (self.button_size[1] + self.spacing) + 80

        self.dialog_rect = Rect(
            (screen_size[0] // 2 - dialog_width // 2,
             screen_size[1] // 2 - dialog_height // 2),
            (dialog_width, dialog_height)
        )

        self._create_buttons()

        close_size = 30
        surf = Surface((close_size, close_size))
        surf.fill((200, 50, 50))
        surf_pressed = Surface((close_size, close_size))
        surf_pressed.fill((255, 80, 80))

        self.close_button = Button(
            init_surface=surf,
            surface_pressed=surf_pressed,
            pos_center=(self.dialog_rect.right - close_size//2 -5,
                        self.dialog_rect.top +  close_size // 2 +10),
            click_type=ClickType.AFTER_RELEASED,
            action=self._close,
            text="X",
            color_text=(255, 255, 255),
            font_size=10
        )

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.dialog_rect.collidepoint(event.pos):
                self._close()

    def _create_buttons(self):
        if self.list_type not in self.data:
            return

        values = self.data[self.list_type]
        x = self.dialog_rect.left + 35
        y = self.dialog_rect.top + 50

        for val, qtd in values.items():
            w, h = self.button_size
            init_surf = Surface((w, h))
            init_surf.fill((220, 220, 220))
            pressed_surf = Surface((w, h))
            pressed_surf.fill((180, 180, 180))

            def make_action(v=val):
                if self.action:
                    self.action(self.list_type,v)
                    self._close()

            btn = Button(
                init_surface=init_surf,
                surface_pressed=pressed_surf,
                pos_center=(x + w // 2, y + h // 2),
                click_type=ClickType.AFTER_RELEASED,
                action=make_action,
                text=f"{self.list_type}: {val} (x{qtd})",
                color_text=(0, 0, 0),
                font_size=10
            )
            self.buttons.append(btn)
            y += h + self.spacing

    def _close(self):
        if self.on_close:
            self.on_close(self)

    def update(self, dt):

        for btn in self.buttons:
            btn.update(dt)
        self.close_button.update(dt)

    def draw(self, surface: Surface):
        overlay = Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (255, 255, 255), self.dialog_rect, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0), self.dialog_rect, 2, border_radius=12)

        font = pygame.font.SysFont(None, 28)
        title_surf = font.render(f"Selecionar {self.list_type}", True, (0, 0, 0))
        surface.blit(title_surf, (self.dialog_rect.centerx - title_surf.get_width() // 2,
                                  self.dialog_rect.top + 15))

        for btn in self.buttons:
            btn.draw(surface)

        self.close_button.draw(surface)
