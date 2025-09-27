from scenes.base_scene import BaseScene
from core.ui.widgets.gesture_detector import GestureDetector, ClickType
from core.ui.widgets.menu_edit_circuit import MenuEditCircuit
from core.ui.widgets.fps_widget import FPSWidget
from pygame import Surface, Rect
from core.systems.circuit_editor.input_system import InputSystem
import pygame

class CircuitEditor(BaseScene):
    def __init__(self, screen: Surface):
        self.screen = screen
        self.width_screen = screen.get_width()
        self.height_screen = screen.get_height()
        super().__init__(self.screen, self.width_screen, self.height_screen)

        self.cell_size = 64
        self.input_system = None
        self.gesture_canvas = None
        self.rects_grid = []

        self.set_gesture_canvas()
        self.set_rects_grid()
        self.input_system = InputSystem(self.entity_mn, self.rects_grid)
        self.set_canvas()

        self.ui_manager.add(
            FPSWidget(),
            MenuEditCircuit(self.input_system, self.screen, self.cell_size)
        )

        self.systems.update([
            self.input_system,
            self.render_system
        ])

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
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DELETE:
                self.input_system.exit_current_tool()

    def update(self, dt):
        self.ui_manager.update(dt)
        self.update_systems(dt)

    def render(self):
        self.screen.fill('white')
        self.screen.blit(self.canvas, (0, 0))
        self.render_system.draw()
        self.ui_manager.draw(self.screen)
