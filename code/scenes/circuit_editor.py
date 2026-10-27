import math
import pygame
from pygame import Rect, Surface

from scenes.base_scene import BaseScene
from core.ui.widgets.gesture_detector import ClickType, GestureDetector
from core.ui.widgets.menu_edit_circuit import MenuEditCircuit
from core.ui.widgets.alert_dialog import AlertDialog
from core.ui.widgets.brush_touch_actions import BrushTouchActions
from core.ui.touch_grid import aim_position, grid_lift_positions
from core.ui.board_view import BoardView
from core.systems.circuit_editor.input_system import InputSystem
from core.managers.node_manager import NodeManager
from core.circuit_tools.circuit_domain import CircuitError
from core.circuit_tools.circuit_entity_mapper import CircuitEntityMapper
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.settings import CELL_SIZE, path_in_circuitos
from core.managers.scene_manager import SceneManager
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.ui.prompt_ui import draw_prompt_hint_row
from core.components.sprite import Sprite
from core.components.dropped import Dropped

# Touch preview of the held part: lighthouse-flame amber where it fits, red where it is blocked.
# (The controller focus keeps its cream; on the white grid a finger-sized preview needs more contrast.)
TOUCH_AIM_OK = (235, 180, 92)
TOUCH_AIM_OK_FILL = (235, 180, 92, 64)
TOUCH_AIM_BLOCKED = (200, 50, 50)
TOUCH_AIM_BLOCKED_FILL = (200, 50, 50, 64)
TOUCH_AIM_OUTLINE_WIDTH = 3
TOUCH_HINT_FONT_SIZE = 14
TOUCH_HINT_TEXT = (245, 230, 170)
TOUCH_HINT_BACKGROUND = (15, 20, 42, 235)
TOUCH_HINT_PADDING = 8
TOUCH_UI_MARGIN = 12
# Circuits are authored on a 20 x 10 board (x up to 1216, y up to 768); smaller screens draw it scaled.
BOARD_COLS = 20
BOARD_MIN_ROWS = 10
BOARD_TOP_CELLS = 2


class CircuitEditor(BaseScene):
    shows_touch_gamepad = False

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
        self._touch_aim: tuple[int, int] | None = None

        self.node_manager = NodeManager()
        self.storage_circuit_manager = StorageCircuitManager()

        self.set_gesture_canvas()
        self.set_entities()
        self.input_system = InputSystem(
            self.entity_mn,
            self.rects_grid,
            self.node_manager,
            self.file,
            self.storage_circuit_manager,
            self.debug_mode,
            pointer_position=self._pointer_position,
        )
        self.set_canvas()
        self.prompt_chip_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)
        self.prompt_text_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)
        self.touch_hint_font = self.resources.load_font("PressStart2P-Regular.ttf", TOUCH_HINT_FONT_SIZE)
        self._touch_hint_cache: dict[str, Surface] = {}

        self.menu_widget = MenuEditCircuit(
            self.input_system,
            self.screen,
            self.cell_size,
            self.ui_manager,
        )
        self.ui_manager.add(self.menu_widget)
        self.brush_touch_actions = BrushTouchActions(
            self.input_system,
            self.menu_widget._button_surface("buttons/wide.png", self.menu_widget.wide_button_size),
            self.menu_widget._button_surface("buttons/wide_pressed.png", self.menu_widget.wide_button_size),
            bottom_left=(TOUCH_UI_MARGIN, self.height_screen - TOUCH_UI_MARGIN),
            input_source=lambda: self.input_manager.last_input_source,
            popup_open=self._has_popup_open,
            font_size=self.menu_widget.top_font_size,
        )
        self.ui_manager.add(self.brush_touch_actions)
        self._fit_board_to_free_area()

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
            # touch acts when the finger lifts (see _act_on_touch_lifts), so the player can aim first
            accepts_touch=False,
        )

    def set_canvas(self):
        self.gesture_canvas.function = self.input_system.handle_canvas_actions
        self.ui_manager.add(self.gesture_canvas)

    def _fit_board_to_free_area(self):
        """Scale the board into the space between the top bar and the sidebar, so no cell hides under them."""
        top = self.cell_size * BOARD_TOP_CELLS
        free_area = Rect(0, top, self.menu_widget.rect_right.left, self.height_screen - top)
        self.board = BoardView((0, top), self.cell_size, BOARD_COLS, BOARD_MIN_ROWS, free_area)

        self.gesture_canvas.rect = Rect(self.board.screen_rect)
        # InputSystem keeps a reference to this list, so refill it instead of replacing it
        self.rects_grid[:] = self.board.world_cells()
        self.grid_cols = self.board.cols
        self.grid_rows = self.board.rows
        self.grid_focus_col = self.grid_cols // 2
        self.grid_focus_row = self.grid_rows // 2

        offset_x, offset_y = self.board.camera_offset
        self.camera.viewport.topleft = (-round(offset_x), -round(offset_y))

        self.canvas = pygame.Surface((self.width_screen, self.height_screen), pygame.SRCALPHA)
        board_rect = self.board.screen_rect
        step = self.board.cell_on_screen
        for x in range(board_rect.left, board_rect.right + 1, step):
            pygame.draw.line(self.canvas, "gray", (x, board_rect.top), (x, board_rect.bottom))
        for y in range(board_rect.top, board_rect.bottom + 1, step):
            pygame.draw.line(self.canvas, "gray", (board_rect.left, y), (board_rect.right, y))

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

        # read before the UI runs: the lift that picks a list item or taps a menu must not also hit the grid
        touch_lift_allowed = self._is_touch() and not self._has_popup_open()
        blocked_rects = self._touch_blocked_rects()

        self.ui_manager.update(dt)
        self.update_systems(dt)
        if touch_lift_allowed:
            self._act_on_touch_lifts(blocked_rects)

    def _pointer_position(self) -> tuple[float, float]:
        """Where the player points, in board coordinates (the board may be drawn scaled)."""
        return self.board.to_world(self._pointer_on_screen())

    def _pointer_on_screen(self) -> tuple[int, int]:
        if not self._is_touch():
            return self.input_manager.get_pointer_position()
        # taps on Rotate/Cancel or the menus must not drag the held part under them
        last_touch = self.input_manager.touch_points.last_position()
        self._touch_aim = aim_position(last_touch, self._touch_blocked_rects(), self._touch_aim or last_touch)
        return self._touch_aim or (0, 0)

    def _is_touch(self) -> bool:
        return self.input_manager.last_input_source == "touch"

    def _touch_blocked_rects(self) -> list[Rect]:
        return [self.menu_widget.rect_top, self.menu_widget.rect_right, *self.brush_touch_actions.rects()]

    def _act_on_touch_lifts(self, blocked_rects: list[Rect]):
        released = self.input_manager.touch_points.released_positions()
        for _ in grid_lift_positions(released, self.gesture_canvas.rect, blocked_rects):
            self.input_system.handle_canvas_actions()

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
        self.render_system.draw(scale=self.board.scale)
        self.ui_manager.draw(self.screen)
        if self._using_controller() and not self._has_popup_open():
            self._draw_grid_focus()
        self._draw_touch_aim()
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
        """The controller-focused cell, in board coordinates."""
        left = self.board.origin[0] + (self.grid_focus_col * self.cell_size)
        top = self.board.origin[1] + (self.grid_focus_row * self.cell_size)
        return Rect(left, top, self.cell_size, self.cell_size)

    def _grid_focus_rect(self) -> Rect:
        w_cells, h_cells = self._brush_footprint_cells()
        anchor = self._grid_anchor_rect()
        return Rect(anchor.left, anchor.top, w_cells * self.cell_size, h_cells * self.cell_size)

    def _sync_mouse_with_grid_focus(self):
        anchor = self.board.to_screen_rect(self._grid_anchor_rect())
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
        focus = self.board.to_screen_rect(self._grid_focus_rect())
        self._draw_area_highlight(focus, self.grid_focus_highlight, self.grid_focus_fill)

    def _draw_area_highlight(self, rect: Rect, outline, fill, width: int = 2):
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill(fill)
        self.screen.blit(overlay, rect.topleft)
        pygame.draw.rect(self.screen, outline, rect.inflate(-width, -width), width)

    def _draw_touch_aim(self):
        """While a finger aims on the grid, light the area the held part will take."""
        brush = self.input_system.brush
        if brush is None or not brush.has(Sprite) or not self._is_touch() or self._has_popup_open():
            return
        blocked = self._touch_blocked_rects()
        aiming = grid_lift_positions(self.input_manager.touch_points.pressed_positions(), self.gesture_canvas.rect, blocked)
        if not aiming:
            return
        area = self.board.to_screen_rect(brush.get(Sprite).rect)
        if brush.has(Dropped) and not self.input_system.can_drop_brush():
            self._draw_area_highlight(area, TOUCH_AIM_BLOCKED, TOUCH_AIM_BLOCKED_FILL, TOUCH_AIM_OUTLINE_WIDTH)
            return
        self._draw_area_highlight(area, TOUCH_AIM_OK, TOUCH_AIM_OK_FILL, TOUCH_AIM_OUTLINE_WIDTH)

    def _draw_touch_hint(self):
        key = "editor_touch_place" if self.input_system.brush is not None else "editor_touch_pick"
        text = LanguageService.get().get_prompt_text(key)
        hint = self._touch_hint_cache.get(text)
        if hint is None:
            label = self.touch_hint_font.render(text, True, TOUCH_HINT_TEXT)
            hint = pygame.Surface(label.get_rect().inflate(TOUCH_HINT_PADDING * 2, TOUCH_HINT_PADDING * 2).size, pygame.SRCALPHA)
            pygame.draw.rect(hint, TOUCH_HINT_BACKGROUND, hint.get_rect(), border_radius=6)
            hint.blit(label, (TOUCH_HINT_PADDING, TOUCH_HINT_PADDING))
            self._touch_hint_cache[text] = hint
        buttons_top = self.height_screen - TOUCH_UI_MARGIN - self.menu_widget.wide_button_size[1]
        self.screen.blit(hint, hint.get_rect(bottomleft=(TOUCH_UI_MARGIN, buttons_top - TOUCH_UI_MARGIN)))

    def _draw_editor_prompt_bar(self):
        if not self.should_draw_bottom_prompt_bar():
            return
        if self._is_touch():
            # key chips mean nothing without a keyboard: say the next step instead
            if not self._has_popup_open():
                self._draw_touch_hint()
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
