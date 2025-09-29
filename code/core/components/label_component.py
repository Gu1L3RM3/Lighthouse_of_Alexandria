# Ficheiro: core/components/label_component.py (versão final)
import pygame
import copy
from core.ecs import Component
from pygame import Vector2
from core.managers import ResourceManager
from core.settings import FONT

class LabelComponent(Component):
    def __init__(self, labels_data: list[dict], font_path: str = FONT):
        super().__init__()
        self.labels_data = labels_data
        self.font_path = font_path

        rm = ResourceManager.get()
        self.font_object = rm.load_font(self.font_path, 10) 
        
        self.rendered_labels = []
        self._render_surfaces()

    def _render_surfaces(self):
        self.rendered_labels.clear()
        for data in self.labels_data:
            self.rendered_labels.append({
                'text': data['text'],
                'color': data['color'],
                'base_offset': Vector2(data.get('base_offset', (0, 0))),
                'surface': self.font_object.render(data['text'], True, data['color'])
            })
            
    def copy(self) -> "LabelComponent":
        return LabelComponent(copy.deepcopy(self.labels_data), self.font_path)

    def to_dict(self) -> dict:
        return {
            'type': self.__class__.__name__,
            'font_path': self.font_path,
            'labels_data': self.labels_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LabelComponent":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
        return cls(labels_data=data['labels_data'], font_path=data['font_path'])