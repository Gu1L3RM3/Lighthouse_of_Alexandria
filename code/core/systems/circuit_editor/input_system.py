import pygame
from pygame import Rect
from core.ecs import System, Entity
from core.managers.entity_manager import EntityManager
from entities.circuit_editor.eletric_components import *
from entities.circuit_editor.edit_components import *
from core.components.position import Position
from core.components.dropped import Dropped
from core.components.always_on_top import AlwaysOnTop
from core.components.sprite import Sprite


class InputSystem(System):
    def __init__(self, entity_manager: EntityManager, grid_rects: list[Rect]):
        super().__init__()
        self.show_mouse = True
        self.select_mode = False
        self.brush: Entity | None = None
        self.active_tool: str | None = None
        self.entity_manager = entity_manager
        self.grid_rects = grid_rects

    def set_brush(self, brush_type: str | None):
        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None
        self.active_tool=brush_type

        brush_map = {
            "resistor": Resistor,
            "wire": Wire,
            "gnd": Ground,
            "sourceI": CurrentSource,
            "sourceV": VoutageSource,
            "select": Select,
            "rotate": Rotate,
            "delete": Delete,
        }

        cls = brush_map.get(brush_type)
        if not cls:
            raise Exception(f"Invalid brush type: {brush_type}")

        x, y = pygame.mouse.get_pos()
        entity: Entity = cls(x, y)
        entity.add(AlwaysOnTop())

        self.entity_manager.add_entity(entity)
        self.brush = entity
        self.show_mouse = False

    def update(self, entity_manager, dt):
        self.update_brush_position()

    def select_entity(self):
        if not isinstance(self.brush, Select):
            return

        target = self.entity_manager.check_collision(self.brush)
        if not target:
            return

        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None

        target.add(AlwaysOnTop())
        self.entity_manager.add_entity(target)
        self.brush = target
        self.show_mouse = False
        self.select_mode = True

    def delete_entity(self):
        if not isinstance(self.brush, Delete):
            return

        target = self.entity_manager.check_collision(self.brush)
        if target:
            self.entity_manager.remove_entity(target)

    def rotate_entity(self):
        if not isinstance(self.brush, Rotate):
            return

        target = self.entity_manager.check_collision(self.brush)
        if not target:
            return

        sprite: Sprite = target.get(Sprite)
        sprite.rotate(90)

    def handle_canvas_actions(self):
        self.drop_entity()
        self.delete_entity()
        self.rotate_entity()
        self.select_entity()

    def drop_entity(self):
        if not self.brush or not self.brush.has(Dropped):
            return

        entities = self.entity_manager.get_entities()
        entities.remove(self.brush)
        rects = [e.get(Sprite).rect for e in entities if e.has(Sprite)]

        sprite: Sprite = self.brush.get(Sprite)
        if sprite.rect.collidelist(rects) != -1:
            return

        new_entity = self.brush.copy()
        new_entity.remove(AlwaysOnTop)
        self.entity_manager.add_entity(new_entity)

        if not self.select_mode:
            return
        self.select_mode = False

        if  self.active_tool == "select":
            self.set_brush('select')
        
        
    def exit_current_tool(self, set_mouse: bool = True):
        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None

        if set_mouse:
            self.show_mouse = True
            pygame.mouse.set_visible(True)

    def update_brush_position(self):
        if not self.brush:
            return

        pos: Position = self.brush.get(Position)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for rect in self.grid_rects:
            if rect.collidepoint((mouse_x, mouse_y)):
                pos.xy = rect.topleft
                return
