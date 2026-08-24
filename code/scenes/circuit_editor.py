import math
import pygame
from pygame import Rect, Surface

from scenes.base_scene import BaseScene
from core.ui.widgets.gesture_detector import ClickType, GestureDetector
from core.ui.widgets.menu_edit_circuit import MenuEditCircuit
from core.ui.widgets.alert_dialog import AlertDialog
from core.systems.circuit_editor.input_system import InputSystem
from core.managers.node_manager import NodeManager
from core.circuit_tools.circuit_domain import CircuitError
from core.circuit_tools.circuit_entity_mapper import CircuitEntityMapper
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.settings import CELL_SIZE, path_in_circuitos
from core.managers.scene_manager import SceneManager
from core.managers.input_manager import InputManager
from core.ui.prompt_ui import draw_prompt_hint_row
from core.components.sprite import Sprite


class CircuitEditor(BaseScene):
    def __init__(
        self,
        screen: Surface,
        file: str = "circuit",
        debug_mode=False,
    ):
        self.screen = screen
        self.debug_mode = debug_mode
        self.width_screen = screen.get_width()
        self.height_screen = screen.get_height()
        super().__init__(self.screen, self.width_screen, self.height_screen)

        self.cell_size = CELL_SIZE
        self.input_system = None
        self.gesture_canvas = None
        self.rects_grid: list[Rect] = []
        self.grid_cols = 0
        self.grid_rows = 0
        self.grid_focus_col = 0
        self.grid_focus_row = 0
        self.grid_focus_highlight = (245, 230, 170)
        self.grid_focus_fill = (245, 230, 170, 48)
        self._grid_repeat_initial = 0.18
        self._grid_repeat_step = 0.09
        self._grid_repeat_cooldown = 0.0
        self._grid_repeat_dir = (0, 0)
        self._menu_nav_cooldown = 0.0
        self._controller_lock_until = 0.0
        self.prompt_chip_font = None
        self.prompt_text_font = None
        self.file = file
        self.input_manager = InputManager.get()

        self.node_manager = NodeManager()
        self.storage_circuit_manager = StorageCircuitManager()

        self.set_gesture_canvas()
        self.set_rects_grid()
        self.set_entities()
        self.input_system = InputSystem(
            self.entity_mn,
            self.rects_grid,
            self.node_manager,
            self.file,
            self.storage_circuit_manager,
            self.debug_mode,
        )
        self.set_canvas()
        self.prompt_chip_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)
        self.prompt_text_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)

        self.menu_widget = MenuEditCircuit(
            self.input_system,
            self.screen,
            self.cell_size,
            self.ui_manager,
        )
        self.ui_manager.add(self.menu_widget)

        self.systems.update([self.input_system, self.render_system])

        self.inputs: dict[int, callable] = {
            pygame.K_n: lambda: self.input_system.set_brush("node"),
            pygame.K_w: lambda: self.input_system.set_brush("wire"),
            pygame.K_g: lambda: self.input_system.set_brush("gnd"),
            pygame.K_r: lambda: self.input_system.rotate_brush(),
            pygame.K_s: lambda: self.input_system.set_brush("select"),
            pygame.K_DELETE: lambda: self.input_system.set_brush("delete"),
            pygame.K_ESCAPE: self.input_system.exit_current_tool,
        }
        if self.debug_mode:
            self.inputs[pygame.K_d] = lambda: self.input_system.set_brush("not_drop")

    def set_entities(self):
        try:
            document = CircuitJsonRepository().load(path_in_circuitos(f"{self.file}.json"))
            initial_entities = CircuitEntityMapper().to_entities(document)
        except CircuitError:
            return
        for entity in initial_entities:
            self.entity_mn.add_entity(entity)
        self.node_manager.rebuild(initial_entities)

    def on_close(self):
        self.ui_manager.remove(self.eletric_list)

    def set_gesture_canvas(self):
        canvas_width = self.cell_size * 20
        canvas_height = self.height_screen
        self.gesture_canvas = GestureDetector(
            (canvas_width, canvas_height),
            function=lambda: None,
            offset=(0, self.cell_size * 2),
            show_debug_surf=False,
            click_type=ClickType.AFTER_PRESSED,
        )

    def set_rects_grid(self):
        left = self.gesture_canvas.rect.left
        top = self.gesture_canvas.rect.top
        cols = self.gesture_canvas.rect.width // self.cell_size
        rows = self.gesture_canvas.rect.height // self.cell_size
        self.grid_cols = cols
        self.grid_rows = rows

        self.rects_grid = [
            Rect(left + x * self.cell_size, top + y * self.cell_size, self.cell_size, self.cell_size)
            for x in range(cols)
            for y in range(rows)
        ]
        self.grid_focus_col = max(0, cols // 2)
        self.grid_focus_row = max(0, rows // 2)

    def set_canvas(self):
        self.gesture_canvas.function = self.input_system.handle_canvas_actions
        self.ui_manager.add(self.gesture_canvas)

        self.canvas = pygame.Surface((self.width_screen, self.height_screen), pygame.SRCALPHA)
        for x in range(0, self.width_screen, self.cell_size):
            pygame.draw.line(self.canvas, "gray", (x, 0), (x, self.height_screen))
        for y in range(0, self.height_screen, self.cell_size):
            pygame.draw.line(self.canvas, "gray", (0, y), (self.width_screen, y))

    def process_input(self, events):
        self._refresh_input_lock(events)
        using_controller = self._using_controller()
        if self.input_manager.is_action_just_pressed("pause"):
            self._exit_editor()
            return

        for event in events:
            self.ui_manager.handle_event(event)
            if event.type == pygame.KEYDOWN and not using_controller:
                func = self.inputs.get(event.key)
                if func:
                    func()

        if using_controller:
            self._process_controller_input()
            return

    def update(self, dt):
        if self._menu_nav_cooldown > 0:
            self._menu_nav_cooldown = max(0.0, self._menu_nav_cooldown - dt)

        if self._using_controller():
            self._update_controller_grid_focus(dt)
            self._sync_mouse_with_grid_focus()
            self.menu_widget.set_controller_navigation(not self._has_popup_open())
            self.input_manager.mouse_visible = False
        else:
            self.menu_widget.set_controller_navigation(False)
            self._update_mouse_visibility_for_pointer()

        self.ui_manager.update(dt)
        self.update_systems(dt)

    def _update_mouse_visibility_for_pointer(self):
        if self._has_popup_open():
            self.input_manager.mouse_visible = True
            return
        brush_active = self.input_system is not None and self.input_system.brush is not None
        if not brush_active:
            self.input_manager.mouse_visible = True
            return
        mouse_pos = pygame.mouse.get_pos()
        on_grid = self.gesture_canvas is not None and self.gesture_canvas.rect.collidepoint(mouse_pos)
        self.input_manager.mouse_visible = not on_grid

    def render(self):
        self.screen.fill("white")
        self.screen.blit(self.canvas, (0, 0))
        self.render_system.draw()
        self.ui_manager.draw(self.screen)
        if self._using_controller() and not self._has_popup_open():
            self._draw_grid_focus()
        self._draw_editor_prompt_bar()

    def _exit_editor(self):
        self.menu_widget.trigger_button("close")

    def _using_controller(self) -> bool:
        if not self.input_manager.has_controller():
            return False
        # Mantem controle ativo mesmo em idle; so troca quando houver intencao explicita de mouse/teclado.
        if self.input_manager.last_input_source == "controller":
            return True
        return (pygame.time.get_ticks() / 1000.0) < self._controller_lock_until

    def _refresh_input_lock(self, events: list[pygame.event.Event]):
        now = pygame.time.get_ticks() / 1000.0
        if self._has_mouse_keyboard_intent(events):
            self._controller_lock_until = 0.0
            return
        if self._has_controller_intent():
            self._controller_lock_until = now + 0.45

    def _has_mouse_keyboard_intent(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            # Nao usar MOUSEMOTION para troca de modo: o controle move mouse virtual.
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                return True
            if event.type == pygame.KEYDOWN and not getattr(event, "synthetic_controller", False):
                return True
        return False

    def _has_controller_intent(self) -> bool:
        if not self.input_manager.has_controller():
            return False
        vector = self.input_manager.get_controller_vector()
        if vector.length_squared() >= 0.7 * 0.7:
            return True
        watched = (
            "confirm",
            "back",
            "open_editor",
            "tool_prev",
            "tool_next",
            "menu_confirm",
            "pause",
            "bomb",
        )
        return any(self.input_manager.is_action_just_pressed(action) for action in watched)

    def _has_modal_open(self) -> bool:
        for widget in reversed(self.ui_manager.widgets):
            if isinstance(widget, AlertDialog):
                return True
        return False

    def _has_popup_open(self) -> bool:
        for widget in reversed(self.ui_manager.widgets):
            if isinstance(widget, AlertDialog):
                return True
            if hasattr(widget, "alert_dialog"):
                return True
        return False

    def _get_top_popup_widget(self):
        for widget in reversed(self.ui_manager.widgets):
            if isinstance(widget, AlertDialog):
                return widget
            if hasattr(widget, "alert_dialog"):
                return widget
        return None

    def _process_controller_input(self):
        if self._has_popup_open():
            self._process_controller_popup_input()
            return

        if self.input_manager.is_action_just_pressed("tool_prev") and self._menu_nav_cooldown <= 0:
            self.menu_widget.move_focus(-1)
            self._menu_nav_cooldown = 0.14
        if self.input_manager.is_action_just_pressed("tool_next") and self._menu_nav_cooldown <= 0:
            self.menu_widget.move_focus(1)
            self._menu_nav_cooldown = 0.14
        if self.input_manager.is_action_just_pressed("menu_confirm"):
            self.menu_widget.activate_focused_button()
        if self.input_manager.is_action_just_pressed("open_editor") and self.input_system.brush:
            self.input_system.rotate_brush()
        if self.input_manager.is_action_just_pressed("back") and self.input_system.brush:
            self.input_system.exit_current_tool()
        if self.input_manager.is_action_just_pressed("confirm"):
            self._activate_grid_focus()

    def _process_controller_popup_input(self):
        popup = self._get_top_popup_widget()
        if popup is None:
            return

        step = self._controller_axis_to_step()
        if hasattr(popup, "controller_move_focus"):
            if step[1] != 0 and self._menu_nav_cooldown <= 0:
                popup.controller_move_focus(step[1])
                self._menu_nav_cooldown = 0.12
            elif step[0] != 0 and self._menu_nav_cooldown <= 0:
                popup.controller_move_focus(step[0])
                self._menu_nav_cooldown = 0.12

        if self.input_manager.is_action_just_pressed("menu_confirm"):
            if hasattr(popup, "controller_activate_focused"):
                popup.controller_activate_focused()
                return
            if hasattr(popup, "confirm_button"):
                popup.confirm_button.activate()
                return

        if self.input_manager.is_action_just_pressed("back"):
            if hasattr(popup, "controller_cancel"):
                popup.controller_cancel()
                return
            if hasattr(popup, "cancel_button"):
                popup.cancel_button.activate()
                return
            if hasattr(popup, "_close"):
                popup._close()

    def _brush_footprint_cells(self) -> tuple[int, int]:
        brush = self.input_system.brush
        if brush is None or not brush.has(Sprite):
            return (1, 1)
        sprite: Sprite = brush.get(Sprite)
        width_px, height_px = sprite.rect.size
        width_px = max(1, int(width_px))
        height_px = max(1, int(height_px))
        return (
            max(1, int(math.ceil(width_px / self.cell_size))),
            max(1, int(math.ceil(height_px / self.cell_size))),
        )

    def _grid_anchor_rect(self) -> Rect:
        left = self.gesture_canvas.rect.left + (self.grid_focus_col * self.cell_size)
        top = self.gesture_canvas.rect.top + (self.grid_focus_row * self.cell_size)
        return Rect(left, top, self.cell_size, self.cell_size)

    def _grid_focus_rect(self) -> Rect:
        w_cells, h_cells = self._brush_footprint_cells()
        anchor = self._grid_anchor_rect()
        return Rect(anchor.left, anchor.top, w_cells * self.cell_size, h_cells * self.cell_size)

    def _sync_mouse_with_grid_focus(self):
        anchor = self._grid_anchor_rect()
        self.input_manager.set_virtual_mouse_position(anchor.center)

    def _move_grid_focus(self, dx: int, dy: int):
        if self.grid_cols <= 0 or self.grid_rows <= 0:
            return
        w_cells, h_cells = self._brush_footprint_cells()
        max_col = max(0, self.grid_cols - w_cells)
        max_row = max(0, self.grid_rows - h_cells)
        self.grid_focus_col = max(0, min(max_col, self.grid_focus_col + dx))
        self.grid_focus_row = max(0, min(max_row, self.grid_focus_row + dy))

    def _controller_axis_to_step(self) -> tuple[int, int]:
        vector = self.input_manager.get_controller_vector()
        threshold = 0.55
        dx = -1 if vector.x <= -threshold else 1 if vector.x >= threshold else 0
        dy = -1 if vector.y <= -threshold else 1 if vector.y >= threshold else 0
        if dx != 0 and dy != 0:
            if abs(vector.x) >= abs(vector.y):
                dy = 0
            else:
                dx = 0
        return dx, dy

    def _update_controller_grid_focus(self, dt: float):
        step = self._controller_axis_to_step()
        if step == (0, 0):
            self._grid_repeat_dir = (0, 0)
            self._grid_repeat_cooldown = 0.0
            return

        if step != self._grid_repeat_dir:
            self._grid_repeat_dir = step
            self._grid_repeat_cooldown = self._grid_repeat_initial
            self._move_grid_focus(step[0], step[1])
            return

        self._grid_repeat_cooldown -= dt
        if self._grid_repeat_cooldown > 0:
            return
        self._grid_repeat_cooldown = self._grid_repeat_step
        self._move_grid_focus(step[0], step[1])

    def _activate_grid_focus(self):
        self._sync_mouse_with_grid_focus()
        self.input_system.handle_canvas_actions()

    def _activate_at_cursor(self):
        mouse_pos = pygame.mouse.get_pos()
        for widget in reversed(self.ui_manager.widgets):
            activate = getattr(widget, "activate_hovered", None)
            if callable(activate) and activate(mouse_pos):
                return
        if self._has_popup_open():
            return
        if self.gesture_canvas.rect.collidepoint(mouse_pos):
            self.input_system.handle_canvas_actions()

    def _draw_grid_focus(self):
        focus_rect = self._grid_focus_rect()
        overlay = pygame.Surface(focus_rect.size, pygame.SRCALPHA)
        overlay.fill(self.grid_focus_fill)
        self.screen.blit(overlay, focus_rect.topleft)
        pygame.draw.rect(self.screen, self.grid_focus_highlight, focus_rect.inflate(-2, -2), 2)

    def _draw_editor_prompt_bar(self):
        if not self.should_draw_bottom_prompt_bar():
            return
        if self._using_controller():
            items = self.input_manager.get_prompt_items("circuit_editor_grid")
        else:
            self.input_manager.last_input_source = "keyboard"
            items = self.input_manager.get_prompt_items("circuit_editor")
        draw_prompt_hint_row(
            self.screen,
            self.prompt_chip_font,
            self.prompt_text_font,
            items,
            anchor=(18, self.height_screen - 24),
            align="left",
        )
