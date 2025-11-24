from core.ecs import Component
from pygame import Vector2
from core.managers.resource_manager import ResourceManager
from core.settings import FONT, LABEL_OFFSET

class LabelComponent(Component):
    def __init__(self, name: str, value: str, font_path: str = FONT,font_size= 10,offset_x = 50,offset_y=LABEL_OFFSET):
        super().__init__()
        self._name = name  
        self._value = value
        self.font_path = font_path

        self.font_size =  font_size
        self.offset_x  = offset_x
        self.offset_y  = offset_y
        self._current =  ""
        self._voltage =  ""

        rm = ResourceManager.get()
        self.font_object = rm.load_font(self.font_path, self.font_size)

        self.rendered_labels = []
        self._render_surfaces()

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
        self.rendered_labels.append({
            'text': self._name,
            'color': 'black',
            'base_offset': Vector2(0, -self.offset_y),
            'surface': self.font_object.render(self._name, True, 'black')
        })
        self.rendered_labels.append({
            'text': self._value,
            'color': 'blue',
            'base_offset': Vector2(0, self.offset_y),
            'surface': self.font_object.render(self._value, True, 'blue')
        })
        self.rendered_labels.append({
            'text':self._voltage,
            'color':'red',
            'base_offset':Vector2(self.offset_x,self.offset_y),
            'surface': self.font_object.render(self._voltage, True, 'red')
        })
        self.rendered_labels.append({
            'text':self._current,
            'color':'red',
            'base_offset':Vector2(self.offset_x,-self.offset_y),
            'surface': self.font_object.render(self._current, True, 'red')
        })

    def copy(self) -> "LabelComponent":
        return LabelComponent(self._name, self._value, self.font_path)

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
    
