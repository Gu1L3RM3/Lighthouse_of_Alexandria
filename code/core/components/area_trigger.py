import pygame
from core.ecs import Component, Entity
from pygame import Rect
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
        active: bool = True,
        on_entered: Optional[Callable[[object], None]] = None,
        on_exit: Optional[Callable[[object], None]] = None,
    ):
        super().__init__()
        # Mantem uma area local ao trigger. O Sprite.rect e mutado no render.
        self.area = area.copy()

        self.active = active
        self.triggered_entities = set()
        self.once = once

        self.on_entered = on_entered
        self.on_exit = on_exit

    def get_rect(self, x, y)->Rect:
        r = self.area.copy()
        r.topleft = (x + self.area.x, y + self.area.y)
        return r

    def check_collision(self, entity: Entity, entity_rect: Rect, area_rect: Rect | None = None):
        if not self.active:
            return

        target_area = area_rect if area_rect is not None else self.area
        in_area = target_area.colliderect(entity_rect)

        if in_area and entity not in self.triggered_entities:
            self.triggered_entities.add(entity)
            if self.on_entered:
                self.on_entered(entity)
            if self.once:
                self.active = False

        elif not in_area and entity in self.triggered_entities:
            self.triggered_entities.remove(entity)
            if self.on_exit:
                self.on_exit(entity)

    def to_dict(self):
        return super().to_dict()
