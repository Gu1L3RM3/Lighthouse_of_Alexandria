import pygame
from pygame import Surface, Rect
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import  ClickType
from core.ui.widgets.button import Button
from core.managers.event_manager import EventManager
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.ui.prompt_ui import draw_prompt_hint_row
from typing import Callable, Optional


class AlertDialog(Widget):
    def __init__(self,
                title:str,
                on_close: Optional[Callable] = None,
                dialog_size:tuple[int,int] = (200,300),
                surface:Surface|None = None,
                parent:Widget|None=None,
                make_freeze:bool= True
                ):
        super().__init__()
        self.title    = title
        self.parent   = parent
        self.surface  = surface
        self.on_close = on_close
        self.make_freeze = make_freeze
        self.buttons: list[Button] = []
        self.screen_size = pygame.display.get_window_size()
        self._dialog_size = (int(dialog_size[0]), int(dialog_size[1]))
        self.input_manager = InputManager.get()
        self.prompt_chip_font = pygame.font.Font(None, 18)
        self.prompt_text_font = pygame.font.Font(None, 18)
        self._closed = False

        self.set_dialog_rect(self._dialog_size)
        if self.make_freeze:
            self.em = EventManager.get()
            self.em.post({'type':'request_freeze','type_request':'AlertDialog'})

        


        self.set_close_button()
    def set_dialog_rect(self,dialog_size:tuple[int,int]):
        if not self.surface:
            self.dialog_rect = Rect(
                (self.screen_size[0] // 2 - dialog_size[0] // 2,
                self.screen_size[1] // 2 - dialog_size[1] // 2),
                (dialog_size[0], dialog_size[1])
                )
            return
        self.dialog_rect =  self.surface.get_rect(center=(self.screen_size[0]//2,
                                                          self.screen_size[1]//2))

    def resize(self, dialog_size: tuple[int, int] | None = None):
        self.screen_size = pygame.display.get_window_size()
        if dialog_size is not None:
            self._dialog_size = (int(dialog_size[0]), int(dialog_size[1]))
        self.set_dialog_rect(self._dialog_size)
        self.set_close_button()

    def set_close_button(self):
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
        elif event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE,
            pygame.K_RETURN,
            pygame.K_SPACE,
        ):
            self._close()



    def _close(self):
        if self._closed:
            return
        self._closed = True
        if self.make_freeze:
            self.em.post({'type':'release_freeze'})
        if not self.on_close:
            return
        if self.parent:
            self.on_close(self.parent)
            return
        self.on_close(self)

    def update(self, dt):
        self.close_button.update(dt)
    def draw_surface(self,surface:Surface):
        if self.surface:
            surface.blit(self.surface,self.dialog_rect)
            return
        
        pygame.draw.rect(surface, (255, 255, 255), self.dialog_rect, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0), self.dialog_rect, 2, border_radius=12)
        font = pygame.font.SysFont(None, 28)
        title_surf = font.render(f"{self.title}", True, (0, 0, 0))
        surface.blit(title_surf, (self.dialog_rect.centerx - title_surf.get_width() // 2,
                                  self.dialog_rect.top + 15))

    def draw(self, surface: Surface):
        overlay = Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        self.draw_surface(surface)


        self.close_button.draw(surface)
        self._draw_close_hint(surface)

    def _draw_close_hint(self, surface: Surface):
        language = LanguageService.get()
        if self.input_manager.last_input_source == "controller":
            items = [
                (self.input_manager.get_prompt_button("confirm"), language.get_prompt_text("close")),
                (self.input_manager.get_prompt_button("back"), language.get_prompt_text("back")),
            ]
        else:
            items = [("ESC", language.get_prompt_text("close")), ("ENTER", language.get_prompt_text("confirm"))]

        draw_prompt_hint_row(
            surface,
            self.prompt_chip_font,
            self.prompt_text_font,
            items,
            anchor=(surface.get_width() - 18, surface.get_height() - 24),
            align="right",
            gap=10,
        )
