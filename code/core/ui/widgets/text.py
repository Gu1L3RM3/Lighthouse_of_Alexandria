from core.ui.widgets.widget import Widget
from core.settings import *
from core.managers.resource_manager import ResourceManager

class Text(Widget):
    def __init__(self,
                 text: str,
                 font_name: str,
                 font_size: int,
                 font_color: tuple[int, int, int] = (255, 255, 255),
                 pos_center: tuple[int, int] = (0, 0)
                 ):
        self.resource_mn = ResourceManager()
        self.font_color = font_color
        self.font = self.resource_mn.load_font(font_name, font_size)
        self.set_text(text, pos_center)

    def draw(self, surface):
        surface.blit(self.surf, self.rect)

    def set_text(self, new_text: str, new_pos_center: tuple[int, int]):
        self.surf = self.font.render(new_text, True, self.font_color)
        self.rect = self.surf.get_rect(center=new_pos_center)

    def update(self, dt):
        pass