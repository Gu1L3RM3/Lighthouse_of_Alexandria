from core.ecs import System, Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.collider import Collider
from core.managers.entity_manager import EntityManager
from typing import List

class PhysicsSystem(System):
    def __init__(self):
        self.static_colliders: List = []  # cache de coliders estáticos

    def cache_static_colliders(self, entity_mn: EntityManager):
        """Chame ao carregar o mapa para armazenar coliders estáticos"""
        collidable_entities = entity_mn.get_entities_with(
            Position, Collider, filter=lambda e: not e.has(Velocity)
        )
        self.static_colliders = [
            e.get(Collider).get_rect(e.get(Position).x, e.get(Position).y)
            for e in collidable_entities
        ]

    def update(self, entity_mn: EntityManager, dt: float):
        # Entidades móveis
        moving_entities = entity_mn.get_entities_with(
            Position, Collider, Velocity,
            filter=lambda e: e.get(Velocity).vel.length_squared() > 0
        )
        for entity in moving_entities:
            self._move_entity(entity, entity_mn, dt)

    def _move_entity(self, entity: Entity, entity_mn: EntityManager, dt: float):
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)
        col: Collider = entity.get(Collider)

        # Movimento em X
        pos.x += vel.vx * dt
        rect = col.get_rect(pos.x, pos.y)
        
        # Colisão com estáticos
        for wall in self.static_colliders:
            if rect.colliderect(wall):
                if vel.vx > 0:
                    rect.right = wall.left
                elif vel.vx < 0:
                    rect.left = wall.right
                vel.vx = 0
                pos.x = rect.x - col.offset_x

        # Colisão com outros móveis (ex.: NPCs)
        for other in entity_mn.get_entities_with(Position, Collider):
            if other.id == entity.id:
                continue
            other_pos = other.get(Position)
            other_col = other.get(Collider).get_rect(other_pos.x, other_pos.y)
            if rect.colliderect(other_col):
                if vel.vx > 0:
                    rect.right = other_col.left
                elif vel.vx < 0:
                    rect.left = other_col.right
                vel.vx = 0
                pos.x = rect.x - col.offset_x

        # Movimento em Y
        pos.y += vel.vy * dt
        rect = col.get_rect(pos.x, pos.y)

        for wall in self.static_colliders:
            if rect.colliderect(wall):
                if vel.vy > 0:
                    rect.bottom = wall.top
                elif vel.vy < 0:
                    rect.top = wall.bottom
                vel.vy = 0
                pos.y = rect.y - col.offset_y

        for other in entity_mn.get_entities_with(Position, Collider):
            if other.id == entity.id:
                continue
            other_pos = other.get(Position)
            other_col = other.get(Collider).get_rect(other_pos.x, other_pos.y)
            if rect.colliderect(other_col):
                if vel.vy > 0:
                    rect.bottom = other_col.top
                elif vel.vy < 0:
                    rect.top = other_col.bottom
                vel.vy = 0
                pos.y = rect.y - col.offset_y
