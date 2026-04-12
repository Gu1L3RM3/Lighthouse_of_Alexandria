import pygame
from pygame import Surface

from core.ui.widgets.widget import Widget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType
from core.systems.circuit_editor.input_system import InputSystem
from core.managers.ui_manager import UIManager
from core.ui.widgets.eletric_list import EletricList
from core.ui.widgets.alert_dialog import AlertDialog
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager


class ConfirmActionDialog(AlertDialog):
    def __init__(self, title: str, on_confirm, on_close, parent: Widget | None = None):
        super().__init__(
            title=title,
            on_close=on_close,
            parent=parent,
            dialog_size=(460, 220),
            make_freeze=False,
        )
        self._on_confirm = on_confirm
        self._build_buttons()

    def _build_buttons(self):
        button_w, button_h = 140, 44
        center_y = self.dialog_rect.bottom - 52
        yes_surface = Surface((button_w, button_h))
        yes_surface.fill((50, 140, 88))
        yes_pressed = Surface((button_w, button_h))
        yes_pressed.fill((72, 168, 112))
        no_surface = Surface((button_w, button_h))
        no_surface.fill((140, 56, 56))
        no_pressed = Surface((button_w, button_h))
        no_pressed.fill((168, 72, 72))

        self.confirm_button = Button(
            init_surface=yes_surface,
            surface_pressed=yes_pressed,
            pos_center=(self.dialog_rect.centerx - 86, center_y),
            click_type=ClickType.AFTER_RELEASED,
            action=self._confirm,
            text="SIM",
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.cancel_button = Button(
            init_surface=no_surface,
            surface_pressed=no_pressed,
            pos_center=(self.dialog_rect.centerx + 86, center_y),
            click_type=ClickType.AFTER_RELEASED,
            action=self._close,
            text="NAO",
            font_size=12,
            color_text=(245, 230, 170),
        )

    def _confirm(self):
        self._on_confirm()
        self._close()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.confirm_button.activate()
                return
            if event.key == pygame.K_ESCAPE:
                self.cancel_button.activate()
                return
        super().handle_events(event)

    def update(self, dt):
        super().update(dt)
        self.confirm_button.update(dt)
        self.cancel_button.update(dt)

    def draw(self, surface: Surface):
        super().draw(surface)
        self.confirm_button.draw(surface)
        self.cancel_button.draw(surface)


class MenuEditCircuit(Widget):
    def __init__(self, input_system: InputSystem, screen: Surface, cell_size: int, ui_manager: UIManager):
        super().__init__()
        self.input_system = input_system
        self.ui_manager = ui_manager
        self.cell_size = cell_size
        self.screen_size = screen.size
        self.rm = ResourceManager.get()
        self.color_background = (0, 0, 0)
        self.screen_width, self.screen_height = self.screen_size
        self.buttons: list[Button] = []
        self.buttons_by_name: dict[str, Button] = {}
        self.top_button_names: list[str] = []
        self.right_button_names: list[str] = []
        self.component_button_names: list[str] = []
        self.action_button_names: list[str] = []
        self.controller_navigation_enabled = False
        self.controller_focus_group = "top"
        self.controller_tab = "components"
        self.focus_index = 0
        self.active_confirmation_dialog: ConfirmActionDialog | None = None
        self.set_eletric_lists()
        self.set_menu_top()
        self.set_menu_right()
        self._refresh_focus_visuals()

    def _register_button(self, name: str, button: Button):
        self.buttons_by_name[name] = button
        self.buttons.append(button)

    def set_eletric_lists(self):
        storage = self.input_system.storage_manager
        data = storage.storage_circuit

        self.resistor_list = EletricList(
            data,
            "Resistor",
            storage_manager=storage,
            action=self.on_eletric_list_click,
            on_close=self.on_close,
        )

        self.v_source_list = EletricList(
            data,
            "VoutageSource",
            storage_manager=storage,
            action=self.on_eletric_list_click,
            on_close=self.on_close,
        )

        self.c_source_list = EletricList(
            data,
            "CurrentSource",
            storage_manager=storage,
            action=self.on_eletric_list_click,
            on_close=self.on_close,
        )

    def on_close(self, widget: Widget):
        self.ui_manager.remove(widget)

    def on_eletric_list_click(self, list_type, value):
        self.input_system.set_brush(list_type, value)

    def to_eletric_list_click(self, eletric_list: Widget):
        self.input_system.exit_current_tool()
        if hasattr(eletric_list, "update_data"):
            eletric_list.update_data()
        self.ui_manager.add(eletric_list)

    def _open_confirmation(self, title: str, on_confirm):
        if self.active_confirmation_dialog is not None:
            return

        def close_dialog(widget):
            dialog = self.active_confirmation_dialog
            if dialog is not None and dialog in self.ui_manager.widgets:
                self.ui_manager.remove(dialog)
            self.active_confirmation_dialog = None

        dialog = ConfirmActionDialog(
            title=title,
            on_confirm=on_confirm,
            on_close=close_dialog,
        )
        self.active_confirmation_dialog = dialog
        self.ui_manager.add(dialog)

    def _request_clear(self):
        self._open_confirmation("LIMPAR TODO O CIRCUITO?", self.input_system.clear_all)

    def _request_exit(self):
        self._open_confirmation("SALVAR E SAIR?", self.exit)

    def set_menu_top(self):
        self.surface_top = Surface((self.screen_width, self.cell_size * 2))
        self.surface_top.fill(self.color_background)

        self.rect_top = self.surface_top.get_rect(topleft=(0, 0))

        surf1 = pygame.transform.scale2x(self.rm.load_image("buttons/wide.png"))
        surf2 = pygame.transform.scale2x(self.rm.load_image("buttons/wide_pressed.png"))
        init_pos_x = self.cell_size * 2
        pos_y = self.cell_size + (self.cell_size / 2) - 15
        font_size = 15

        self._register_button(
            "node",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("node"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x, pos_y),
                text="Node",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("node")
        self.component_button_names.append("node")
        self._register_button(
            "v_source",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.to_eletric_list_click(self.v_source_list),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 3, pos_y),
                text="V Source",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("v_source")
        self.component_button_names.append("v_source")
        self._register_button(
            "resistor",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.to_eletric_list_click(self.resistor_list),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 6, pos_y),
                text="Resistor",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("resistor")
        self.component_button_names.append("resistor")
        self._register_button(
            "i_source",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.to_eletric_list_click(self.c_source_list),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 9, pos_y),
                text="I Source",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("i_source")
        self.component_button_names.append("i_source")
        self._register_button(
            "gnd",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("gnd"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 12, pos_y),
                text="GND",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("gnd")
        self.component_button_names.append("gnd")
        self._register_button(
            "wire",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("wire"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 15, pos_y),
                text="Wire",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("wire")
        self.component_button_names.append("wire")

        surf1 = pygame.transform.scale2x(self.rm.load_image("buttons/short.png"))
        surf2 = pygame.transform.scale2x(self.rm.load_image("buttons/short_pressed.png"))
        self._register_button(
            "close",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=self._request_exit,
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(init_pos_x + self.cell_size * 17, pos_y - 5),
                text="X",
                font_size=font_size,
            ),
        )
        self.top_button_names.append("close")
        self.action_button_names.append("close")

    def exit(self):
        try:
            self.input_system.save_circuit()
        except Exception:
            pass
        SceneManager.get().back_with_fade()

    def set_menu_right(self):
        self.surface_right = Surface((self.cell_size * 2, self.screen_height))

        self.surface_right.fill(self.color_background)
        pos_x_menu_right = self.screen_width - self.cell_size - 22
        self.rect_right = self.surface_right.get_rect(topleft=(pos_x_menu_right, 0))

        surf1 = pygame.transform.scale2x(self.rm.load_image("buttons/short.png"))
        surf2 = pygame.transform.scale2x(self.rm.load_image("buttons/short_pressed.png"))

        font_size = 15

        pos_x = pos_x_menu_right + 40
        start_y = self.cell_size

        self._register_button(
            "rotate",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("rotate"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y),
                text="R",
                font_size=font_size,
            ),
        )
        self.right_button_names.append("rotate")
        self.action_button_names.append("rotate")
        self._register_button(
            "delete",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("delete"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y + self.cell_size * 2),
                text="D",
                font_size=font_size,
            ),
        )
        self.right_button_names.append("delete")
        self.action_button_names.append("delete")
        self._register_button(
            "select",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=lambda: self.input_system.set_brush("select"),
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y + self.cell_size * 4),
                text="S",
                font_size=font_size,
            ),
        )
        self.right_button_names.append("select")
        self.action_button_names.append("select")
        self._register_button(
            "save",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=self.input_system.save_circuit,
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y + self.cell_size * 6),
                text="Solve",
                font_size=font_size,
            ),
        )
        self.right_button_names.append("save")
        self.action_button_names.append("save")
        self._register_button(
            "load",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=self.input_system.load_circuit,
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y + self.cell_size * 8),
                text="Load",
                font_size=font_size,
            ),
        )
        self.right_button_names.append("load")
        self.action_button_names.append("load")
        self._register_button(
            "clear",
            Button(
                click_type=ClickType.AFTER_PRESSED,
                action=self._request_clear,
                init_surface=surf1.copy(),
                surface_pressed=surf2.copy(),
                pos_center=(pos_x, start_y + self.cell_size * 10),
                text="Clear",
                font_size=font_size - 2,
            ),
        )
        self.right_button_names.append("clear")
        self.action_button_names.append("clear")

    def trigger_button(self, name: str, trigger_action: bool = True) -> bool:
        button = self.buttons_by_name.get(name)
        if button is None:
            return False
        if self.controller_navigation_enabled:
            self.focus_button(name)
        button.activate(trigger_action=trigger_action)
        return True

    def set_controller_navigation(self, enabled: bool):
        if self.controller_navigation_enabled == enabled:
            return
        self.controller_navigation_enabled = enabled
        if enabled and self.focus_index >= len(self.buttons):
            self.focus_index = 0
        self._refresh_focus_visuals()

    def _buttons_in_group(self, group: str) -> list[str]:
        return self.top_button_names if group == "top" else self.right_button_names

    def _buttons_in_tab(self, tab: str) -> list[str]:
        return self.component_button_names if tab == "components" else self.action_button_names

    def _active_group_buttons(self) -> list[str]:
        return self._buttons_in_group(self.controller_focus_group)

    def _set_focus_by_group_index(self, group: str, index: int):
        names = self._buttons_in_group(group)
        if not names:
            return
        index = max(0, min(len(names) - 1, index))
        self.controller_focus_group = group
        self.focus_button(names[index])

    def move_focus_horizontal(self, step: int):
        names = self._active_group_buttons()
        if not names:
            return
        focused_name = None
        for name in names:
            button = self.buttons_by_name.get(name)
            if button and self.buttons.index(button) == self.focus_index:
                focused_name = name
                break
        if focused_name is None:
            focused_name = names[0]
        current_index = names.index(focused_name)
        next_index = (current_index + step) % len(names)
        self._set_focus_by_group_index(self.controller_focus_group, next_index)

    def set_controller_tab(self, tab: str):
        if tab not in ("components", "actions"):
            return
        self.controller_tab = tab
        names = self._buttons_in_tab(tab)
        if not names:
            return
        self.focus_button(names[0])

    def switch_controller_tab(self, step: int):
        tabs = ("components", "actions")
        current_idx = tabs.index(self.controller_tab) if self.controller_tab in tabs else 0
        next_tab = tabs[(current_idx + step) % len(tabs)]
        self.set_controller_tab(next_tab)

    def move_focus_in_tab(self, step: int):
        names = self._buttons_in_tab(self.controller_tab)
        if not names:
            return
        focused_name = names[0]
        for name in names:
            button = self.buttons_by_name.get(name)
            if button and self.buttons.index(button) == self.focus_index:
                focused_name = name
                break
        current_idx = names.index(focused_name)
        next_idx = (current_idx + step) % len(names)
        self.focus_button(names[next_idx])

    def move_focus_vertical(self, step: int):
        source_group = self.controller_focus_group
        target_group = "right" if source_group == "top" and step > 0 else "top" if source_group == "right" and step < 0 else source_group
        if target_group == source_group:
            if source_group == "right":
                self.move_focus_horizontal(step)
            return
        source_names = self._buttons_in_group(source_group)
        target_names = self._buttons_in_group(target_group)
        if not source_names or not target_names:
            return
        focused_name = source_names[0]
        for name in source_names:
            button = self.buttons_by_name.get(name)
            if button and self.buttons.index(button) == self.focus_index:
                focused_name = name
                break
        source_button = self.buttons_by_name[focused_name]
        source_y = source_button._rect.centery
        nearest = min(
            target_names,
            key=lambda name: abs(self.buttons_by_name[name]._rect.centery - source_y),
        )
        self.controller_focus_group = target_group
        self.focus_button(nearest)

    def move_focus(self, step: int):
        if not self.buttons:
            return
        self.focus_index = (self.focus_index + step) % len(self.buttons)
        self._sync_focus_group_from_index()
        self._refresh_focus_visuals()

    def focus_button(self, name: str):
        button = self.buttons_by_name.get(name)
        if button is None:
            return
        try:
            self.focus_index = self.buttons.index(button)
        except ValueError:
            return
        self._sync_focus_group_from_index()
        self._refresh_focus_visuals()

    def _sync_focus_group_from_index(self):
        if not self.buttons:
            return
        current_button = self.buttons[self.focus_index]
        for name, button in self.buttons_by_name.items():
            if button is current_button:
                if name in self.component_button_names:
                    self.controller_tab = "components"
                elif name in self.action_button_names:
                    self.controller_tab = "actions"
                if name in self.top_button_names:
                    self.controller_focus_group = "top"
                elif name in self.right_button_names:
                    self.controller_focus_group = "right"
                return

    def focus_tool(self, tool: str | None):
        if not tool:
            return
        mapping = {
            "node": "node",
            "wire": "wire",
            "gnd": "gnd",
            "select": "select",
            "delete": "delete",
            "rotate": "rotate",
        }
        button_name = mapping.get(tool)
        if button_name:
            self.focus_button(button_name)

    def get_focused_button_name(self) -> str | None:
        if not self.buttons:
            return None
        focused = self.buttons[self.focus_index]
        for name, button in self.buttons_by_name.items():
            if button is focused:
                return name
        return None

    def activate_focused_button(self) -> str | None:
        if not self.buttons:
            return None
        name = self.get_focused_button_name()
        self.buttons[self.focus_index].activate()
        return name

    def _refresh_focus_visuals(self):
        for idx, button in enumerate(self.buttons):
            button.set_focused(self.controller_navigation_enabled and idx == self.focus_index)

    def set_mouse(self):
        # A visibilidade do mouse e controlada centralmente pelo InputManager.
        return

    def update(self, dt):
        self.set_mouse()
        for button in self.buttons:
            button.update(dt)
        self._refresh_focus_visuals()

    def activate_hovered(self, mouse_pos: tuple[int, int]) -> bool:
        for button in self.buttons:
            if button._rect.collidepoint(mouse_pos):
                button.activate()
                return True
        return False

    def draw(self, surface):
        surface.blit(self.surface_top, self.rect_top)
        surface.blit(self.surface_right, self.rect_right)
        for button in self.buttons:
            button.draw(surface)
