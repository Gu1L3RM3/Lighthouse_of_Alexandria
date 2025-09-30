from core.ecs import Component
from pygame import Vector2
from core.managers import ResourceManager
from core.settings import FONT, LABEL_OFFSET

class LabelComponent(Component):
    def __init__(self, name: str, value: str, font_path: str = FONT):
        super().__init__()
        self.name = name
        self.value = value
        self.font_path = font_path

        rm = ResourceManager.get()
        self.font_object = rm.load_font(self.font_path, 10)

        self.rendered_labels = []
        self._render_surfaces()

    def _render_surfaces(self):
        self.rendered_labels.clear()
        self.rendered_labels.append({
            'text': self.name,
            'color': 'black',
            'base_offset': Vector2(0, -LABEL_OFFSET),
            'surface': self.font_object.render(self.name, True, 'black')
        })
        self.rendered_labels.append({
            'text': self.value,
            'color': 'blue',
            'base_offset': Vector2(0, LABEL_OFFSET),
            'surface': self.font_object.render(self.value, True, 'blue')
        })

    def copy(self) -> "LabelComponent":
        return LabelComponent(self.name, self.value, self.font_path)

    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'font_path': self.font_path,
            'name': self.name,
            'value': self.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LabelComponent":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
        return cls(name=data['name'], value=data['value'], font_path=data['font_path'])
