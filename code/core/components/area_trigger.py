import pygame
from core.ecs import Component
from pygame import Rect, Surface
from typing import Callable, Optional


class AreaTrigger(Component):
    """
    Componente inspirado no 'Area2D' da Godot.
    Detecta quando outras entidades entram ou saem da área e dispara callbacks.
    """

    def __init__(
        self,
        area: Rect,
        once: bool = False,
        active : bool =True,
        on_entered:Optional[Callable[[object], None]]=None,
        on_exit:Optional[Callable[[object], None]]=None,
    ):
        super().__init__()
        self.area = area

        self.active = active
        self.triggered_entities = set()
        self.once = once

        self.on_entered = on_entered
        self.on_exit    = on_exit





    def check_collision(self, entity_id: int, entity_rect: Rect):
        """Verifica se a entidade entrou ou saiu da área."""
        if not self.active:
            return

        in_area = self.area.colliderect(entity_rect)

        
        if in_area and entity_id not in self.triggered_entities:
            self.triggered_entities.add(entity_id)

            if self.on_entered:
                self.on_entered(entity_id)



            if self.once:
                self.active = False


        elif not in_area and entity_id in self.triggered_entities:
            self.triggered_entities.remove(entity_id)

            if self.on_exit:
                self.on_exit(entity_id)



    def to_dict(self):
        return super().to_dict()
    
