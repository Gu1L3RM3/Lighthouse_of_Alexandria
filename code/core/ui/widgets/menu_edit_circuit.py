from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import *
from core.systems.circuit_editor.input_system import InputSystem
from core.managers.ui_manager import UIManager
from core.ui.widgets.eletric_list import EletricList
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager
class MenuEditCircuit(Widget):
    def __init__(self, input_system: InputSystem,screen:Surface,cell_size:int,ui_manager:UIManager):
        super().__init__()
        self.input_system = input_system
        self.ui_manager=ui_manager
        self.cell_size = cell_size
        self.screen_size=screen.size
        self.rm=ResourceManager.get()
        self.color_background= (0,0,0)
        self.screen_width, self.screen_height = self.screen_size
        self.buttons = []  
        self.set_eletric_lists()
        self.set_menu_top()
        self.set_menu_right()


    def set_eletric_lists(self):
        storage = self.input_system.storage_manager
        data = storage.storage_circuit

        self.resistor_list = EletricList(data, "Resistor",
                                        storage_manager=storage,
                                        action=self.on_eletric_list_click,
                                        on_close=self.on_close)

        self.v_source_list = EletricList(data, "VoutageSource",
                                        storage_manager=storage,
                                        action=self.on_eletric_list_click,
                                        on_close=self.on_close)

        self.c_source_list = EletricList(data, "CurrentSource",
                                        storage_manager=storage,
                                        action=self.on_eletric_list_click,
                                        on_close=self.on_close)
        

    def on_close(self,widget:Widget):
        self.ui_manager.remove(widget)
        

    def on_eletric_list_click(self,list_type, value):
        self.input_system.set_brush(list_type,value)
    def to_eletric_list_click(self,eletric_list:Widget):
        self.input_system.exit_current_tool()
        if hasattr(eletric_list, "update_data"):
            eletric_list.update_data()
        self.ui_manager.add(eletric_list)
    def set_menu_top(self):
        self.surface_top = Surface((self.screen_width,self.cell_size*2))
        self.surface_top.fill(self.color_background)

        self.rect_top =  self.surface_top.get_rect(topleft=(0,0))


        
        surf1 = pygame.transform.scale2x(self.rm.load_image('buttons/wide.png'),)
        surf2 = pygame.transform.scale2x(self.rm.load_image('buttons/wide_pressed.png'))
        init_pos_x = self.cell_size*2
        pos_y = self.cell_size+(self.cell_size/2)-15
        font_size = 15
        
        self.node_button =Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("node"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x, pos_y),
            text="Node",
            font_size=font_size,
        )
        self.source_V_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.to_eletric_list_click(self.v_source_list),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*3, pos_y),
            text="V Source",
            font_size=font_size,
        )
        self.resistor_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.to_eletric_list_click(self.resistor_list),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*6, pos_y),
            text="Resistor",
            font_size=font_size,
        )
        self.source_I_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.to_eletric_list_click(self.c_source_list),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*9, pos_y),
            text="I Source",
            font_size=font_size,
        )
        self.ground_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("gnd"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*12, pos_y),
            text="GND",
            font_size=font_size,
        )
        self.wire_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush("wire"),
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*15, pos_y),
            text="Wire",
            font_size=font_size,
        )

        surf1 =  pygame.transform.scale2x(self.rm.load_image('buttons/short.png'))
        surf2 =  pygame.transform.scale2x(self.rm.load_image('buttons/short_pressed.png'),)
        self.close_button =Button(
            click_type=ClickType.AFTER_PRESSED,
            action=self.exit,
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(init_pos_x+self.cell_size*17, pos_y-5),
            text="X",
            font_size=font_size,
        )

        self.buttons.extend([
            self.node_button,
            self.source_V_button,
            self.resistor_button,
            self.source_I_button,
            self.ground_button,
            self.wire_button,
            self.close_button
        ])

    def exit(self):
        try:
            self.input_system.save_circuit()
        except Exception:
            pass
        SceneManager.get().back_with_fade()
    def set_menu_right(self):
        self.surface_right = Surface((self.cell_size*2,self.screen_height))
        
        self.surface_right.fill(self.color_background)
        pos_x_menu_right=self.screen_width - self.cell_size -22
        self.rect_right =  self.surface_right.get_rect(topleft=(pos_x_menu_right,0))

        surf1 =  pygame.transform.scale2x(self.rm.load_image('buttons/short.png'))
        surf2 =  pygame.transform.scale2x(self.rm.load_image('buttons/short_pressed.png'),)

        font_size = 15

        
        pos_x = pos_x_menu_right+40
        start_y = self.cell_size


        self.rotate_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda: self.input_system.set_brush('rotate'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x,start_y),
            text="R",
            font_size=font_size,
        )
        self.delete_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda : self.input_system.set_brush('delete'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*2),
            text="D",
            font_size=font_size,
        )
        self.select_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=lambda : self.input_system.set_brush('select'),  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*4),
            text="S",
            font_size=font_size,
        )
        self.save_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=self.input_system.save_circuit,  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*6),
            text="Save",
            font_size=font_size,
        )
        self.load_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=self.input_system.load_circuit,  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*8),
            text="Load",
            font_size=font_size,
        )
        self.clear_button = Button(
            click_type=ClickType.AFTER_PRESSED,
            action=self.input_system.clear_all,  
            init_surface=surf1.copy(),
            surface_pressed=surf2.copy(),
            pos_center=(pos_x, start_y + self.cell_size*10),
            text="Clear",
            font_size=font_size-2,
        )


        self.buttons.extend([
            self.rotate_button,
            self.delete_button,
            self.select_button,
            self.save_button,
            self.load_button,
            self.clear_button
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
