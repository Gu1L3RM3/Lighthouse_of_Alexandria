from scenes.base_scene import BaseScene
from core.ui.widgets.gesture_detector import GestureDetector, ClickType
from core.ui.widgets.menu_edit_circuit import MenuEditCircuit
from pygame import Surface, Rect
from core.systems.circuit_editor.input_system import InputSystem
from core.managers.node_manager import NodeManager
from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
import pygame
from core.settings import CELL_SIZE
from core.managers.input_manager import InputManager
from core.managers.scene_manager import SceneManager
from core.ui.prompt_ui import draw_prompt_hint_row

class CircuitEditor(BaseScene):
    def __init__(self, screen: Surface,
                 file:str='circuit',
                 debug_mode =  False,
                 ):
        
        self.screen = screen
        self.debug_mode =  debug_mode
        self.width_screen = screen.get_width()
        self.height_screen = screen.get_height()
        super().__init__(self.screen, self.width_screen, self.height_screen)

        self.cell_size = CELL_SIZE
        self.input_system = None
        self.gesture_canvas = None
        self.rects_grid = []
        self.input_manager = InputManager.get()
        self.controller_cursor_speed = 620.0
        self.controller_tool_cycle = ["node", "wire", "gnd", "select", "delete"]
        self.prompt_chip_font = None
        self.prompt_text_font = None

        self.file =  file
 

        self.node_manager = NodeManager()
        self.storage_circuit_manager = StorageCircuitManager()

        self.set_gesture_canvas()
        self.set_rects_grid()
        self.set_entities()
        self.input_system = InputSystem(self.entity_mn,
                                        self.rects_grid,
                                        self.node_manager,
                                        self.file,
                                        self.storage_circuit_manager,
                                        self.debug_mode,
                                        )
        self.set_canvas()
        self.prompt_chip_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)
        self.prompt_text_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)

        
        self.ui_manager.add(
            MenuEditCircuit(self.input_system,
                            self.screen,
                            self.cell_size,
                            self.ui_manager),
            
        )

        self.systems.update([
            self.input_system,
            self.render_system
        ])

        

        self.inputs:dict[int,callable] ={
            pygame.K_n:lambda:self.input_system.set_brush("node"),
            pygame.K_w:lambda:self.input_system.set_brush("wire"),
            pygame.K_g:lambda:self.input_system.set_brush("gnd"),
            pygame.K_r:lambda:self.input_system.rotate_brush(),
            pygame.K_s:lambda:self.input_system.set_brush("select"),
            pygame.K_DELETE:lambda:self.input_system.set_brush("delete"),
            pygame.K_ESCAPE:self.input_system.exit_current_tool,

        }
        if self.debug_mode:
            self.inputs[pygame.K_d] = lambda: self.input_system.set_brush('not_drop')
    
    def set_entities(self):
        initial_entities = SerializationManager.load_entities_from_json(f'{self.file}.json')
        if not initial_entities:
            return
        for entity in initial_entities:
            self.entity_mn.add_entity(entity)
            self.node_manager.add_node(entity)
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
            click_type=ClickType.AFTER_PRESSED
        )

    def set_rects_grid(self):
        left = self.gesture_canvas.rect.left
        top = self.gesture_canvas.rect.top
        cols = self.gesture_canvas.rect.width // self.cell_size
        rows = self.gesture_canvas.rect.height // self.cell_size

        self.rects_grid = [
            Rect(left + x * self.cell_size, top + y * self.cell_size, self.cell_size, self.cell_size)
            for x in range(cols)
            for y in range(rows)
        ]

    def set_canvas(self):
        self.gesture_canvas.function = self.input_system.handle_canvas_actions
        self.ui_manager.add(self.gesture_canvas)

        self.canvas = pygame.Surface((self.width_screen, self.height_screen), pygame.SRCALPHA)

        for x in range(0, self.width_screen, self.cell_size):
            pygame.draw.line(self.canvas, 'gray', (x, 0), (x, self.height_screen))

        for y in range(0, self.height_screen, self.cell_size):
            pygame.draw.line(self.canvas, 'gray', (0, y), (self.width_screen, y))

    def process_input(self, events):
        if self.input_manager.is_action_just_pressed("pause"):
            self._exit_editor()
            return

        for event in events:
            self.ui_manager.handle_event(event)
            if event.type == pygame.JOYBUTTONDOWN:
                if self._handle_controller_shortcut(event.button):
                    continue
            if event.type == pygame.KEYDOWN:
                func = self.inputs.get(event.key)
                if func : func()
        if self.input_manager.is_action_just_pressed("confirm"):
            self._activate_at_cursor()

    def update(self, dt):
        self._update_controller_cursor(dt)
        self.ui_manager.update(dt)
        self.update_systems(dt)

    def render(self):
        self.screen.fill('white')
        self.screen.blit(self.canvas, (0, 0))
        self.render_system.draw()
        self.ui_manager.draw(self.screen)
        self._draw_editor_prompt_bar()
        self._draw_controller_cursor()

    def _exit_editor(self):
        for widget in self.ui_manager.widgets:
            if isinstance(widget, MenuEditCircuit):
                widget.exit()
                return
        SceneManager.get().back_with_fade()

    def _activate_at_cursor(self):
        mouse_pos = pygame.mouse.get_pos()
        for widget in reversed(self.ui_manager.widgets):
            activate = getattr(widget, "activate_hovered", None)
            if callable(activate) and activate(mouse_pos):
                return
        if self.gesture_canvas.rect.collidepoint(mouse_pos):
            self.input_system.handle_canvas_actions()

    def _update_controller_cursor(self, dt: float):
        if not self.input_manager.has_controller():
            return
        direction = self.input_manager.get_controller_vector()
        if direction.length_squared() == 0:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        new_x = mouse_x + (direction.x * self.controller_cursor_speed * dt)
        new_y = mouse_y + (direction.y * self.controller_cursor_speed * dt)
        clamped_x = max(0, min(self.width_screen - 1, int(new_x)))
        clamped_y = max(0, min(self.height_screen - 1, int(new_y)))
        self.input_manager.set_virtual_mouse_position((clamped_x, clamped_y))

    def _draw_controller_cursor(self):
        if self.input_manager.last_input_source != "controller":
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        color = (36, 52, 92)
        outline = (232, 208, 132)
        pygame.draw.circle(self.screen, outline, (mouse_x, mouse_y), 11, 2)
        pygame.draw.line(self.screen, color, (mouse_x - 6, mouse_y), (mouse_x + 6, mouse_y), 2)
        pygame.draw.line(self.screen, color, (mouse_x, mouse_y - 6), (mouse_x, mouse_y + 6), 2)

    def _draw_editor_prompt_bar(self):
        if not self.should_draw_bottom_prompt_bar():
            return
        items = self.input_manager.get_prompt_items("circuit_editor")
        if not items:
            return
        draw_prompt_hint_row(
            self.screen,
            self.prompt_chip_font,
            self.prompt_text_font,
            items,
            anchor=(18, self.height_screen - 24),
            align="left",
        )

    def _handle_controller_shortcut(self, button: int) -> bool:
        if button == 1:
            self.input_system.exit_current_tool()
            return True
        if button == 2:
            self.input_system.set_brush("wire")
            return True
        if button == 3:
            if self.input_system.brush:
                self.input_system.rotate_brush()
            else:
                self.input_system.set_brush("rotate")
            return True
        if button == 4:
            self._cycle_tool(-1)
            return True
        if button == 5:
            self._cycle_tool(1)
            return True
        return False

    def _cycle_tool(self, step: int):
        active_tool = self.input_system.active_tool
        if active_tool not in self.controller_tool_cycle:
            next_tool = self.controller_tool_cycle[0 if step >= 0 else -1]
        else:
            current_index = self.controller_tool_cycle.index(active_tool)
            next_tool = self.controller_tool_cycle[(current_index + step) % len(self.controller_tool_cycle)]
        self.input_system.set_brush(next_tool)
