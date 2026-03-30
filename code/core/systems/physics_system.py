from core.ecs import System, Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.collider import Collider
from core.components.freeze import Freeze
from core.components.dynamic_collision import DynamicCollision
from core.managers.entity_manager import EntityManager
from typing import List
import pygame


class PhysicsSystem(System):
    def __init__(self):
        self.static_colliders: List[pygame.Rect] = []

    def cache_static_colliders(self, entity_mn: EntityManager):
        """Armazena os colisores estaticos (paredes/obstaculos fixos)."""
        collidable_entities = entity_mn.get_entities_with(
            Position, Collider, filter=lambda e: not e.has(Velocity)
        )
        self.static_colliders = [
            e.get(Collider).get_rect(e.get(Position).x, e.get(Position).y)
            for e in collidable_entities
        ]

    def update(self, entity_mn: EntityManager, dt: float):
        """Atualiza posicao e colisoes das entidades em movimento."""
        moving_entities = entity_mn.get_entities_with(Position, Velocity)

        for entity in moving_entities:
            if entity.has(Freeze):
                freeze: Freeze = entity.get(Freeze)
                if freeze.active:
                    continue

            if not entity.has(Collider):
                self._move(entity, dt)
                continue

            self._move_with_collision(entity, moving_entities, dt)

    def _move(self, entity: Entity, dt: float):
        """Movimento sem colisao (entidade livre)."""
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)

        pos.x += vel.vx * dt
        pos.y += vel.vy * dt

    def _move_with_collision(self, entity: Entity, moving_entities: List[Entity], dt: float):
        """Movimento com verificacao de colisao eixo por eixo."""
        vel: Velocity = entity.get(Velocity)

        if vel.vx != 0:
            self._move_axis(entity, vel.vx * dt, 0, moving_entities)

        if vel.vy != 0:
            self._move_axis(entity, 0, vel.vy * dt, moving_entities)

    def _has_dynamic_collision_enabled(self, entity: Entity) -> bool:
        if not entity.has(DynamicCollision):
            return True
        dyn: DynamicCollision = entity.get(DynamicCollision)
        return dyn.enabled

    def _should_ignore_dynamic_collision(self, entity: Entity, other: Entity) -> bool:
        # Aranhas devem atravessar umas às outras para evitar travamentos de rota.
        if getattr(entity, "enemy_kind", None) == "spider" and getattr(other, "enemy_kind", None) == "spider":
            return True
        return (
            (not self._has_dynamic_collision_enabled(entity))
            or (not self._has_dynamic_collision_enabled(other))
        )

    def _move_axis(self, entity: Entity, dx: float, dy: float, moving_entities: List[Entity]):
        """Move a entidade em um eixo e resolve colisoes com estaticos e dinamicos."""
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)
        col: Collider = entity.get(Collider)

        pos.x += dx
        pos.y += dy

        rect = col.get_rect(pos.x, pos.y)

        for wall in self.static_colliders:
            if rect.colliderect(wall):
                rect, vel = self._resolve_collision(rect, wall, dx, dy, vel, col)
                pos.x = rect.x - col.offset_x
                pos.y = rect.y - col.offset_y
                return

        for other in moving_entities:
            if other is entity or not other.has(Collider):
                continue
            if self._should_ignore_dynamic_collision(entity, other):
                continue

            other_pos = other.get(Position)
            other_col = other.get(Collider)
            other_rect = other_col.get_rect(other_pos.x, other_pos.y)

            if rect.colliderect(other_rect):
                rect, vel = self._resolve_collision(rect, other_rect, dx, dy, vel, col)
                pos.x = rect.x - col.offset_x
                pos.y = rect.y - col.offset_y
                return

    def _resolve_collision(self, rect, other_rect, dx, dy, vel, col):
        """Resolve colisao ajustando posicao e zerando velocidade."""
        if dx > 0:
            rect.right = other_rect.left
            vel.vx = 0
        elif dx < 0:
            rect.left = other_rect.right
            vel.vx = 0
        elif dy > 0:
            rect.bottom = other_rect.top
            vel.vy = 0
        elif dy < 0:
            rect.top = other_rect.bottom
            vel.vy = 0

        return rect, vel
