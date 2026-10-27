from typing import Callable

from pygame import Rect, Surface

from core.components.connectable import Connectable
from core.managers.language_service import LanguageService
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType
from core.ui.widgets.widget import Widget

BUTTON_GAP = 12


class BrushTouchActions(Widget):
    """Rotate and Cancel for a part held by touch: the R and ESC keys of players without a keyboard."""

    def __init__(
        self,
        input_system,
        idle_surface: Surface,
        pressed_surface: Surface,
        bottom_left: tuple[int, int],
        input_source: Callable[[], str],
        popup_open: Callable[[], bool],
        font_size: int = 12,
    ):
        super().__init__()
        self.input_system = input_system
        self._input_source = input_source
        self._popup_open = popup_open
        language = LanguageService.get()
        actions = {
            "rotate": (input_system.rotate_brush, "editor_rotate_brush"),
            "cancel": (input_system.exit_current_tool, "editor_cancel_tool"),
        }
        width, height = idle_surface.get_size()
        left, bottom = bottom_left
        # Fixed slots: Cancel keeps its place when Rotate is hidden, so the thumb finds it.
        self.buttons: dict[str, Button] = {}
        for slot, (name, (action, label_key)) in enumerate(actions.items()):
            self.buttons[name] = Button(
                init_surface=idle_surface.copy(),
                surface_pressed=pressed_surface.copy(),
                pos_center=(left + width // 2 + slot * (width + BUTTON_GAP), bottom - height // 2),
                click_type=ClickType.AFTER_RELEASED,
                action=action,
                text=language.get_ui_label(label_key),
                font_size=font_size,
            )
        self._visible: list[str] = []

    def visible_button_names(self) -> list[str]:
        return list(self._visible)

    def rects(self) -> list[Rect]:
        """Where the buttons cover the grid, so a finger lifted there is not a placement."""
        return [self.buttons[name]._rect for name in self._visible]

    def update(self, dt):
        self._visible = self._buttons_to_show()
        for name in self._visible:
            self.buttons[name].update(dt)

    def draw(self, surface: Surface):
        for name in self._visible:
            self.buttons[name].draw(surface)

    def _buttons_to_show(self) -> list[str]:
        brush = self.input_system.brush
        if brush is None or self._input_source() != "touch" or self._popup_open():
            return []
        if brush.has(Connectable):
            return ["rotate", "cancel"]
        return ["cancel"]
