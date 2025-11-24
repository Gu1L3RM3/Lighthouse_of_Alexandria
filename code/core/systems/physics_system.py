from core.ecs import System, Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.collider import Collider
from core.components.freeze import Freeze
from core.managers.entity_manager import EntityManager
from typing import List
import pygame



class PhysicsSystem(System):
    def __init__(self):
        self.static_colliders: List[pygame.Rect] = []

    def cache_static_colliders(self, entity_mn: EntityManager):
        """Armazena os colisores estáticos (paredes/obstáculos fixos)."""
        collidable_entities = entity_mn.get_entities_with(
            Position, Collider, filter=lambda e: not e.has(Velocity)
        )
        self.static_colliders = [
            e.get(Collider).get_rect(e.get(Position).x, e.get(Position).y)
            for e in collidable_entities
        ]

    def update(self, entity_mn: EntityManager, dt: float):
        """Atualiza posição e colisões das entidades em movimento."""
        
        moving_entities = entity_mn.get_entities_with(Position, Velocity)

        for entity in moving_entities:
            if entity.has(Freeze):
                freeze: Freeze = entity.get(Freeze)
                if freeze.active:
                    continue

            if not entity.has(Collider):
                self._move(entity, dt)
                continue

            
            # passa lista de entidades móveis para colisão dinâmica
            self._move_with_collision(entity, moving_entities, dt)

    def _move(self, entity: Entity, dt: float):
        """Movimento sem colisão (entidade livre)."""
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)

        pos.x += vel.vx * dt
        pos.y += vel.vy * dt

    def _move_with_collision(self, entity: Entity, moving_entities: List[Entity], dt: float):
        """Movimento com verificação de colisão eixo por eixo."""
        vel: Velocity = entity.get(Velocity)

        if vel.vx != 0:
            self._move_axis(entity, vel.vx * dt, 0, moving_entities)

        if vel.vy != 0:
            self._move_axis(entity, 0, vel.vy * dt, moving_entities)

    def _move_axis(self, entity: Entity, dx: float, dy: float, moving_entities: List[Entity]):
        """Move a entidade em um eixo e resolve colisões com estáticos e dinâmicos."""
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)
        col: Collider = entity.get(Collider)

        pos.x += dx
        pos.y += dy

        rect = col.get_rect(pos.x, pos.y)

        # --- colisão com estáticos ---
        for wall in self.static_colliders:
            if rect.colliderect(wall):
                rect, vel = self._resolve_collision(rect, wall, dx, dy, vel, col)
                pos.x = rect.x - col.offset_x
                pos.y = rect.y - col.offset_y
                return  

        # --- colisão com outras entidades móveis ---
        for other in moving_entities:
            if other is entity or not other.has(Collider):
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
        """Resolve colisão ajustando posição e zerando velocidade."""
        if dx > 0:  # direita
            rect.right = other_rect.left
            vel.vx = 0

        elif dx < 0:  # esquerda
            rect.left = other_rect.right
            vel.vx = 0

        elif dy > 0:  # baixo
            rect.bottom = other_rect.top
            vel.vy = 0

        elif dy < 0:  # cima
            rect.top = other_rect.bottom
            vel.vy = 0

        return rect, vel
