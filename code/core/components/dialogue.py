import pygame
from pygame import Rect
from pygame import Surface
from core.ui.widgets.type_writer import TypewriterEffect
from core.managers.resource_manager import ResourceManager
from core.ecs import Component

class Dialogue(Component):
    def __init__(self, lines: list[str],size_dialogue:tuple[int,int],auto_start:bool=False,active_status:bool=True):
        self.lines = lines
        self.current_index = 0
        self.active_status =  active_status
        self.active = False
        self.typewriter = None
        self.size_dialogue=size_dialogue
        self.auto_start =  auto_start
        self.rm=ResourceManager.get()
        self.triggered=False
        self.dialog_box_rect = None
        self.wrapped_lines = [] 
        self.font = None
        self.font_color = (255, 255, 255)
        self.max_text_width = 0
    def get_area(self,x:int,y:int):
        return Rect(
            x,
            y,
            self.size_dialogue[0],
            self.size_dialogue[1]
        )
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        return lines

    def _prepare_dialogue(self, screen_size, font_name, font_size, font_color):
        
        self.font_color = font_color
        padding = 40
        self.max_text_width = screen_size[0] - (padding * 3)
        
        
        self.font = self.rm.load_font(font_name,font_size) 

        raw_text = self.lines[self.current_index]
        self.wrapped_lines = self._wrap_text(raw_text, self.font, self.max_text_width)

        line_height = self.font.get_linesize()
        box_height = (len(self.wrapped_lines) * line_height) + padding
        box_width = self.max_text_width + padding
        
        
        box_x = (screen_size[0] - box_width) / 2
        box_y = (screen_size[1]+600 - box_height) / 2 

        self.dialog_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        typewriter_text = "\n".join(self.wrapped_lines)
        
        text_center_pos = self.dialog_box_rect.center
        self.typewriter = TypewriterEffect(
            text_center_pos, typewriter_text, font_name, font_size, font_color, speed=30
        )

    def start(self, screen_size, font_name="PressStart2P-Regular.ttf", font_size=16, font_color=(255,255,255)):
        self.active = True
        self.current_index = 0
        self._prepare_dialogue(screen_size, font_name, font_size, font_color)

    def next(self, screen_size, font_name="PressStart2P-Regular.ttf", font_size=16, font_color=(255,255,255)):
        self.current_index += 1
        if self.current_index >= len(self.lines):
            self.active = False
            return False
        self._prepare_dialogue(screen_size, font_name, font_size, font_color)
        return True

    def update(self,dt):
        if self.typewriter:
            self.typewriter.update(dt)

    def draw(self, surface: Surface):
        if not self.active or not self.dialog_box_rect:
            return

        pygame.draw.rect(surface, (10, 20, 40), self.dialog_box_rect, border_radius=8)
        pygame.draw.rect(surface, (200, 220, 255), self.dialog_box_rect, 2, border_radius=8)
        
        
       
        self.typewriter.draw(surface)
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'lines':self.lines
        }
            
    