from core.ecs import Component
import pygame
from pygame import Vector2
from core.managers.resource_manager import ResourceManager
from core.settings import FONT, LABEL_OFFSET

class LabelComponent(Component):
    def __init__(
        self,
        name: str,
        value: str,
        font_path: str = FONT,
        font_size=10,
        offset_x=50,
        offset_y=LABEL_OFFSET,
        name_color='black',
        value_color='blue',
        aux_color='red',
        use_outline=False,
        outline_color=(18, 22, 28),
    ):
        super().__init__()
        self._name = name  
        self._value = value
        self.font_path = font_path

        self.font_size =  font_size
        self.offset_x  = offset_x
        self.offset_y  = offset_y
        self._current =  ""
        self._voltage =  ""
        self.name_color = name_color
        self.value_color = value_color
        self.aux_color = aux_color
        self.use_outline = use_outline
        self.outline_color = outline_color

        rm = ResourceManager.get()
        self.font_object = rm.load_font(self.font_path, self.font_size)

        self.rendered_labels = []
        self._render_surfaces()

    def _render_text(self, text: str, color) -> pygame.Surface:
        if text is None:
            text = ""
        text = str(text)
        base = self.font_object.render(text, True, color)
        if not self.use_outline or not text:
            return base

        outlined = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        shadow = self.font_object.render(text, True, self.outline_color)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
            outlined.blit(shadow, (dx, dy))
        outlined.blit(base, (1, 1))
        return outlined

    @property
    def value(self)->str:
        return self._value
    @value.setter
    def value(self,value:str):
        self._value = value
        self._render_surfaces()
    @property
    def name(self) -> str:
        return self._name

    
    @name.setter
    def name(self, name: str):
        self._name = name
        self._render_surfaces()

    @property
    def voltage(self)->str:
        return self._voltage
    @voltage.setter
    def voltage(self,voltage:str):
        self._voltage = voltage
        self._render_surfaces()
    @property
    def current(self)->str:
        return self._current
    @current.setter
    def current(self,current:str):
        self._current = current
        self._render_surfaces()

    def _render_surfaces(self):
        self.rendered_labels.clear()
        if self._name:
            self.rendered_labels.append({
                'text': self._name,
                'color': self.name_color,
                'base_offset': Vector2(0, -self.offset_y),
                'surface': self._render_text(self._name, self.name_color)
            })
        if self._value:
            self.rendered_labels.append({
                'text': self._value,
                'color': self.value_color,
                'base_offset': Vector2(0, self.offset_y),
                'surface': self._render_text(self._value, self.value_color)
            })
        if self._voltage:
            self.rendered_labels.append({
                'text':self._voltage,
                'color':self.aux_color,
                'base_offset':Vector2(self.offset_x,self.offset_y),
                'surface': self._render_text(self._voltage, self.aux_color)
            })
        if self._current:
            self.rendered_labels.append({
                'text':self._current,
                'color':self.aux_color,
                'base_offset':Vector2(self.offset_x,-self.offset_y),
                'surface': self._render_text(self._current, self.aux_color)
            })

    def copy(self) -> "LabelComponent":
        return LabelComponent(
            self._name,
            self._value,
            self.font_path,
            self.font_size,
            self.offset_x,
            self.offset_y,
            self.name_color,
            self.value_color,
            self.aux_color,
            self.use_outline,
            self.outline_color,
        )

    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'font_path': self.font_path,
            'name': self._name,
            'value': self._value
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LabelComponent":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
        return cls(name=data['name'], value=data['value'], font_path=data['font_path'])
    
