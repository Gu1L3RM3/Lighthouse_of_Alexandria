import pygame
from pygame import Surface, Rect
from typing import Callable, Optional

from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import ClickType
from core.ui.widgets.button import Button
from core.managers.resource_manager import ResourceManager
from core.ui.widgets.alert_dialog import AlertDialog
from core.settings import (
    ELETRIC_LIST_DIALOG_MAX_SCREEN_RATIO,
    ELETRIC_LIST_DIALOG_MIN_HEIGHT,
    ELETRIC_LIST_DIALOG_SIDE_PADDING,
    ELETRIC_LIST_DIALOG_TOP_PADDING,
    ELETRIC_LIST_DIALOG_BOTTOM_PADDING,
    ELETRIC_LIST_SCROLL_STEP,
)


class EletricList(Widget):
    DIALOG_MAX_SCREEN_RATIO = ELETRIC_LIST_DIALOG_MAX_SCREEN_RATIO
    DIALOG_MIN_HEIGHT = ELETRIC_LIST_DIALOG_MIN_HEIGHT
    DIALOG_SIDE_PADDING = ELETRIC_LIST_DIALOG_SIDE_PADDING
    DIALOG_TOP_PADDING = ELETRIC_LIST_DIALOG_TOP_PADDING
    DIALOG_BOTTOM_PADDING = ELETRIC_LIST_DIALOG_BOTTOM_PADDING
    SCROLL_STEP = ELETRIC_LIST_SCROLL_STEP

    def __init__(
        self,
        data: dict,
        list_type: str,
        storage_manager,
        button_size: tuple[int, int] = (220, 50),
        spacing: int = 10,
        action: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
    ):
        super().__init__()
        self.data = data
        self.storage_manager = storage_manager
        self.list_type = list_type
        self.button_size = (int(button_size[0]), int(button_size[1]))
        self.spacing = int(spacing)
        self.action = action
        self.on_close = on_close
        self.buttons: list[Button] = []
        self.visible_buttons: list[Button] = []
        self.rm = ResourceManager.get()
        self.scroll_offset = 0
        self.content_view_rect = Rect(0, 0, 0, 0)
        self.content_height = 0
        self._last_revision = self.storage_manager.revision
        self.controller_focus_index = 0

        self.set_alert_dialog()
        self._create_buttons()

    def _compute_content_height(self, num_items: int) -> int:
        if num_items <= 0:
            return 0
        return num_items * self.button_size[1] + (num_items - 1) * self.spacing

    def _compute_dialog_size(self, num_items: int) -> tuple[int, int]:
        dialog_width = self.button_size[0] + (self.DIALOG_SIDE_PADDING * 2)
        content_height = self._compute_content_height(num_items)
        desired_height = self.DIALOG_TOP_PADDING + content_height + self.DIALOG_BOTTOM_PADDING
        screen_h = pygame.display.get_window_size()[1]
        max_height = int(screen_h * self.DIALOG_MAX_SCREEN_RATIO)
        dialog_height = max(self.DIALOG_MIN_HEIGHT, min(desired_height, max_height))
        return dialog_width, dialog_height

    def _update_content_rect(self):
        width = max(1, self.alert_dialog.dialog_rect.width - (self.DIALOG_SIDE_PADDING * 2))
        height = max(1, self.alert_dialog.dialog_rect.height - self.DIALOG_TOP_PADDING - self.DIALOG_BOTTOM_PADDING)
        self.content_view_rect = Rect(
            self.alert_dialog.dialog_rect.left + self.DIALOG_SIDE_PADDING,
            self.alert_dialog.dialog_rect.top + self.DIALOG_TOP_PADDING,
            width,
            height,
        )

    def _max_scroll(self) -> int:
        return max(0, self.content_height - self.content_view_rect.height)

    def _clamp_scroll(self):
        self.scroll_offset = max(0, min(self.scroll_offset, self._max_scroll()))

    def _set_scroll(self, value: int):
        old_value = self.scroll_offset
        self.scroll_offset = int(value)
        self._clamp_scroll()
        if self.scroll_offset != old_value:
            self._create_buttons()

    def _scroll_by(self, delta: int):
        self._set_scroll(self.scroll_offset + delta)

    def set_alert_dialog(self):
        num_items = len(self.data.get(self.list_type, {}))
        dialog_size = self._compute_dialog_size(num_items)
        self.content_height = self._compute_content_height(num_items)
        if not hasattr(self, "alert_dialog"):
            self.alert_dialog = AlertDialog(
                dialog_size=dialog_size,
                on_close=self.on_close,
                title=f"{self.list_type} List",
                parent=self,
                make_freeze=False,
            )
        else:
            self.alert_dialog.resize(dialog_size)
        self._update_content_rect()
        self._clamp_scroll()

    def _create_buttons(self):
        self.buttons.clear()
        self.visible_buttons.clear()
        self.controller_focus_index = 0
        if self.list_type not in self.data:
            return

        values = self.data[self.list_type]
        if not values:
            return

        x_center = self.content_view_rect.centerx
        y = self.content_view_rect.top - self.scroll_offset

        for val, qtd in values.items():
            w, h = self.button_size
            color = (220, 220, 220) if qtd > 0 else (160, 160, 160)
            pressed_color = (180, 180, 180) if qtd > 0 else (120, 120, 120)

            init_surf = Surface((w, h))
            init_surf.fill(color)
            pressed_surf = Surface((w, h))
            pressed_surf.fill(pressed_color)

            def make_action(v=val, q=qtd):
                if q == 0:
                    return
                if self.action:
                    self.action(self.list_type, v)
                    if self.on_close:
                        self.on_close(self)

            btn = Button(
                init_surface=init_surf,
                surface_pressed=pressed_surf,
                pos_center=(x_center, y + h // 2),
                click_type=ClickType.AFTER_RELEASED,
                action=make_action,
                text=f"{self.list_type}: {val} (x{qtd})",
                color_text=(0, 0, 0),
                font_size=10,
            )
            self.buttons.append(btn)
            y += h + self.spacing

        self._update_visible_buttons()
        self._clamp_controller_focus()

    def _update_visible_buttons(self):
        self.visible_buttons = [
            button for button in self.buttons if button._rect.colliderect(self.content_view_rect)
        ]
        self._clamp_controller_focus()

    def _clamp_controller_focus(self):
        if not self.buttons:
            self.controller_focus_index = 0
            return
        self.controller_focus_index = max(0, min(len(self.buttons) - 1, self.controller_focus_index))

    def _focused_button(self) -> Button | None:
        if not self.buttons:
            return None
        self._clamp_controller_focus()
        return self.buttons[self.controller_focus_index]

    def _ensure_focus_visible(self):
        btn = self._focused_button()
        if btn is None:
            return
        if btn._rect.top < self.content_view_rect.top:
            self._set_scroll(self.scroll_offset - (self.content_view_rect.top - btn._rect.top))
        elif btn._rect.bottom > self.content_view_rect.bottom:
            self._set_scroll(self.scroll_offset + (btn._rect.bottom - self.content_view_rect.bottom))

    def controller_move_focus(self, step: int):
        if not self.buttons:
            return
        self.controller_focus_index = (self.controller_focus_index + step) % len(self.buttons)
        self._ensure_focus_visible()
        self._update_visible_buttons()

    def controller_activate_focused(self) -> bool:
        btn = self._focused_button()
        if btn is None:
            return False
        btn.activate()
        return True

    def controller_cancel(self):
        if self.on_close:
            self.on_close(self)

    def update_data(self):
        self.data = self.storage_manager.storage_circuit
        self.set_alert_dialog()
        self._create_buttons()
        self._last_revision = self.storage_manager.revision

    def handle_events(self, event):
        self.alert_dialog.handle_events(event)
        mouse_pos = pygame.mouse.get_pos()
        inside_list = self.content_view_rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEWHEEL and inside_list:
            self._scroll_by(-event.y * self.SCROLL_STEP)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and inside_list:
            if event.button == 4:
                self._scroll_by(-self.SCROLL_STEP)
            elif event.button == 5:
                self._scroll_by(self.SCROLL_STEP)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._scroll_by(-self.SCROLL_STEP)
            elif event.key == pygame.K_DOWN:
                self._scroll_by(self.SCROLL_STEP)
            elif event.key == pygame.K_PAGEUP:
                self._scroll_by(-int(self.content_view_rect.height * 0.8))
            elif event.key == pygame.K_PAGEDOWN:
                self._scroll_by(int(self.content_view_rect.height * 0.8))
            elif event.key == pygame.K_HOME:
                self._set_scroll(0)
            elif event.key == pygame.K_END:
                self._set_scroll(self._max_scroll())

    def update(self, dt):
        if self._last_revision != self.storage_manager.revision:
            self.update_data()

        self._update_visible_buttons()
        for btn in self.visible_buttons:
            btn.update(dt)
        self.alert_dialog.update(dt)

    def activate_hovered(self, mouse_pos: tuple[int, int]) -> bool:
        for btn in self.visible_buttons:
            if btn._rect.collidepoint(mouse_pos):
                btn.activate()
                return True
        return False

    def _draw_scrollbar(self, surface: Surface):
        max_scroll = self._max_scroll()
        if max_scroll <= 0:
            return

        track = Rect(
            self.content_view_rect.right - 6,
            self.content_view_rect.top,
            6,
            self.content_view_rect.height,
        )
        pygame.draw.rect(surface, (65, 65, 65), track, border_radius=3)

        visible_ratio = self.content_view_rect.height / max(1, self.content_height)
        thumb_height = max(20, int(track.height * visible_ratio))
        thumb_travel = max(1, track.height - thumb_height)
        thumb_y = track.top + int((self.scroll_offset / max_scroll) * thumb_travel)
        thumb = Rect(track.left, thumb_y, track.width, thumb_height)
        pygame.draw.rect(surface, (220, 220, 220), thumb, border_radius=3)

    def draw(self, surface: Surface):
        self.alert_dialog.draw(surface)

        previous_clip = surface.get_clip()
        surface.set_clip(self.content_view_rect)
        for btn in self.visible_buttons:
            btn.draw(surface)
        surface.set_clip(previous_clip)

        focused = self._focused_button()
        if focused is not None and focused in self.visible_buttons:
            pygame.draw.rect(surface, (245, 230, 170), focused._rect.inflate(6, 6), 2, border_radius=4)

        self._draw_scrollbar(surface)
