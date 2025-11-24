from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import ClickType
from core.ui.widgets.button import Button
from core.managers.resource_manager import ResourceManager
from typing import Callable, Optional
from core.ui.widgets.alert_dialog import AlertDialog

class EletricList(Widget):
    def __init__(self,
                 data: dict,
                 list_type: str,
                 storage_manager,
                 button_size: tuple[int, int] = (220, 50),
                 spacing: int = 10,
                 action: Optional[Callable] = None,
                 on_close: Optional[Callable] = None):
        super().__init__()
        self.data = data
        self.storage_manager = storage_manager
        self.list_type = list_type
        self.button_size = (int(button_size[0]), int(button_size[1]))
        self.spacing = int(spacing)
        self.action = action
        self.on_close = on_close
        self.buttons: list[Button] = []
        self.rm = ResourceManager.get()
        self._last_revision = self.storage_manager.revision

        self.set_alert_dialog()
        self._create_buttons()

    def set_alert_dialog(self):
        num_items = len(self.data.get(self.list_type, {}))
        dialog_width = self.button_size[0] + 80
        dialog_height = num_items * (self.button_size[1] + self.spacing) + 80
        self.alert_dialog = AlertDialog(
            dialog_size=(dialog_width, dialog_height),
            on_close=self.on_close,
            title=f"{self.list_type} List",
            parent=self,
            make_freeze=False
        )

    def _create_buttons(self):
        self.buttons.clear()
        if self.list_type not in self.data:
            return

        values = self.data[self.list_type]
        x = self.alert_dialog.dialog_rect.left + 35
        y = self.alert_dialog.dialog_rect.top + 50

        for val, qtd in values.items():
            w, h = self.button_size
            # Define cores diferentes se o componente estiver indisponível
            color = (220, 220, 220) if qtd > 0 else (160, 160, 160)
            pressed_color = (180, 180, 180) if qtd > 0 else (120, 120, 120)

            init_surf = Surface((w, h))
            init_surf.fill(color)
            pressed_surf = Surface((w, h))
            pressed_surf.fill(pressed_color)

            # Só cria ação se a quantidade for maior que 0
            def make_action(v=val, q=qtd):
                if q == 0:
                    return  # não faz nada
                if self.action:
                    self.action(self.list_type, v)
                    self.on_close(self)

            btn = Button(
                init_surface=init_surf,
                surface_pressed=pressed_surf,
                pos_center=(x + w // 2, y + h // 2),
                click_type=ClickType.AFTER_RELEASED,
                action=make_action,
                text=f"{self.list_type}: {val} (x{qtd})",
                color_text=(0, 0, 0),
                font_size=10,
            )
            self.buttons.append(btn)
            y += h + self.spacing

    def update_data(self):
        """Recria os botões com base nos dados atualizados."""
        self._create_buttons()
        self._last_revision = self.storage_manager.revision

    def handle_events(self, event):
        self.alert_dialog.handle_events(event)

    def update(self, dt):
        # Detecta mudanças no armazenamento
        if self._last_revision != self.storage_manager.revision:
            self.update_data()

        for btn in self.buttons:
            btn.update(dt)
        self.alert_dialog.update(dt)

    def draw(self, surface: Surface):
        self.alert_dialog.draw(surface)
        for btn in self.buttons:
            btn.draw(surface)
