from core.ecs import System, Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.collider import Collider
from core.managers.entity_manager import EntityManager
from typing import List
import pygame


class PhysicsSystem(System):
    def __init__(self):
        self.static_colliders: List[pygame.Rect] = []

    def cache_static_colliders(self, entity_mn: EntityManager):
        collidable_entities = entity_mn.get_entities_with(
            Position, Collider, filter=lambda e: not e.has(Velocity)
        )
        self.static_colliders = [
            e.get(Collider).get_rect(e.get(Position).x, e.get(Position).y)
            for e in collidable_entities
        ]

    def update(self, entity_mn: EntityManager, dt: float):
        moving_entities = entity_mn.get_entities_with(
            Position, Velocity,
            filter=lambda e: e.get(Velocity).vel.length_squared() > 0
        )

        for entity in moving_entities:
            
            if not entity.has(Collider):
                self._move(entity, dt)
                continue
            
            self._move_with_collision(entity, entity_mn, dt)

    def _move(self, entity: Entity, dt: float):
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)

        pos.x += vel.vx * dt
        pos.y += vel.vy * dt

    def _move_with_collision(self, entity: Entity, entity_mn: EntityManager, dt: float):
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)
        col: Collider = entity.get(Collider)

      
        pos.x += vel.vx * dt
        rect = col.get_rect(pos.x, pos.y)

        idx = rect.collidelist(self.static_colliders)
        if idx != -1: 
            wall = self.static_colliders[idx]
            if vel.vx > 0:
                rect.right = wall.left
            elif vel.vx < 0:
                rect.left = wall.right
            vel.vx = 0
            pos.x = rect.x - col.offset_x

        other_rects = [
            other.get(Collider).get_rect(other.get(Position).x, other.get(Position).y)
            for other in entity_mn.get_entities_with(Position, Collider)
            if other.id != entity.id
        ]
        idx = rect.collidelist(other_rects)
        if idx != -1:
            other_col = other_rects[idx]
            if vel.vx > 0:
                rect.right = other_col.left
            elif vel.vx < 0:
                rect.left = other_col.right
            vel.vx = 0
            pos.x = rect.x - col.offset_x

        pos.y += vel.vy * dt
        rect = col.get_rect(pos.x, pos.y)

        idx = rect.collidelist(self.static_colliders)
        if idx != -1:
            wall = self.static_colliders[idx]
            if vel.vy > 0:
                rect.bottom = wall.top
            elif vel.vy < 0:
                rect.top = wall.bottom
            vel.vy = 0
            pos.y = rect.y - col.offset_y

        other_rects = [
            other.get(Collider).get_rect(other.get(Position).x, other.get(Position).y)
            for other in entity_mn.get_entities_with(Position, Collider)
            if other.id != entity.id
        ]
        idx = rect.collidelist(other_rects)
        if idx != -1:
            other_col = other_rects[idx]
            if vel.vy > 0:
                rect.bottom = other_col.top
            elif vel.vy < 0:
                rect.top = other_col.bottom
            vel.vy = 0
            pos.y = rect.y - col.offset_y
