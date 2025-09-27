from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import *
from core.systems.circuit_editor.input_system import InputSystem

class MenuEditCircuit(Widget):
    def __init__(self, input_system: InputSystem,screen:Surface,cell_size:int):
        super().__init__()
        self.input_system = input_system

        self.cell_size = cell_size
        self.screen_width, self.screen_height = screen.size
        self.buttons = []  

        self.set_menu_top()
        self.set_menu_right()

    def set_menu_top(self):
        self.surface_top = Surface((self.screen_width,self.cell_size*2))
        self.surface_top.fill('white')

        self.rect_top =  self.surface_top.get_rect(topleft=(0,0))


        
        surf1 = Surface(((self.cell_size/2)*4, self.cell_size))
        surf1.fill('blue')
        surf2 = Surface(((self.cell_size/2)*4, self.cell_size))
        surf2.fill((50, 50, 50))

        init_pos_x = self.cell_size*2
        pos_y = self.cell_size+(self.cell_size/2)
        font_size = 15

        self.source_V_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("sourceV"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x, pos_y),
            color=(0, 100, 188),
            text="V Source",
            font_size=font_size,
        )
        self.resistor_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("resistor"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x*3, pos_y),
            color=(200, 170, 10),
            text="Resistor",
            font_size=font_size,
        )
        self.source_I_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("sourceI"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x*5, pos_y),
            color=(20, 100, 10),
            text="I Source",
            font_size=font_size,
        )
        self.ground_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("gnd"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x*7, pos_y),
            color=(100, 150, 200),
            text="GND",
            font_size=font_size,
        )
        self.wire_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("wire"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x*9, pos_y),
            color=(30, 60, 70),
            text="Wire",
            font_size=font_size,
        )

        self.buttons.extend([
            self.source_V_button,
            self.resistor_button,
            self.source_I_button,
            self.ground_button,
            self.wire_button
        ])

    def set_menu_right(self):
        self.surface_right = Surface((self.cell_size*2,self.screen_height))
        
        self.surface_right.fill('white')
        pos_x_menu_right=self.screen_width - self.cell_size -22
        self.rect_right =  self.surface_right.get_rect(topleft=(pos_x_menu_right,0))

        surf1 = Surface((self.cell_size, self.cell_size))
        surf1.fill('blue')
        surf2 = Surface((self.cell_size, self.cell_size))
        surf2.fill((50, 50, 50))

        font_size = 15

        
        pos_x = pos_x_menu_right+32
        start_y = self.cell_size*3

        
        self.rotate_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush('rotate'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x,start_y),
            color=(200, 120, 50),
            text="R",
            font_size=font_size,
        )
        self.delete_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda : self.input_system.set_brush('delete'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*2),
            color=(200, 50, 50),
            text="D",
            font_size=font_size,
        )
        self.select_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda : self.input_system.set_brush('select'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*4),
            color=(200, 150, 150),
            text="S",
            font_size=font_size,
        )

        self.buttons.extend([

            self.rotate_button,
            self.delete_button,
            self.select_button,
        ])

    def set_mouse(self):
        mouse_pos= pygame.mouse.get_pos()
        if self.rect_top.collidepoint(mouse_pos):
            pygame.mouse.set_visible(True)
            return
        if self.rect_right.collidepoint(mouse_pos):
            pygame.mouse.set_visible(True)
            return
        pygame.mouse.set_visible(self.input_system.show_mouse)
    def update(self, dt):
        self.set_mouse()
        for button in self.buttons:
            button.update(dt)

    def draw(self, surface):
        surface.blit(self.surface_top,self.rect_top)
        surface.blit(self.surface_right,self.rect_right)
        for button in self.buttons:
            button.draw(surface)
