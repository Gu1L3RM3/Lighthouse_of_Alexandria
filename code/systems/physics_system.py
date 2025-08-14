from core.ecs import System, Entity
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.collider import Collider
from typing import List


class PhysicsSystem(System):
    def update(self, entities: List[Entity], dt: float):
        moving_entities = []
        colliders = []

        # Classifica entidades
        for e in entities:
            if not e.has(Collider) or not e.has(Position):
                continue

            col :Collider= e.get(Collider)
            pos :Position= e.get(Position)

            if e.has(Velocity) and e.get(Velocity).vel.length_squared() > 0:
                moving_entities.append(e)
            else:
                colliders.append(col.get_rect(pos.x, pos.y))

        # Atualiza entidades móveis
        for entity in moving_entities:
            self._move_entity(entity, colliders, dt)

    def _move_entity(self, entity: Entity, colliders: List, dt: float):
        """Move entidade em X e Y tratando colisões separadamente."""
        pos: Position = entity.get(Position)
        vel: Velocity = entity.get(Velocity)
        col: Collider = entity.get(Collider)

        # Movimento em X
        pos.x += vel.vx * dt
        rect = col.get_rect(pos.x, pos.y)
        for wall in colliders:
            if rect.colliderect(wall):
                if vel.vx > 0:   # Indo para a direita
                    rect.right = wall.left
                elif vel.vx < 0: # Indo para a esquerda
                    rect.left = wall.right
                vel.vx = 0
                pos.x = rect.x - col.offset_x

        # Movimento em Y
        pos.y += vel.vy * dt
        rect = col.get_rect(pos.x, pos.y)
        for wall in colliders:
            if rect.colliderect(wall):
                if vel.vy > 0:   # Indo para baixo
                    rect.bottom = wall.top
                elif vel.vy < 0: # Indo para cima
                    rect.top = wall.bottom
                vel.vy = 0
                pos.y = rect.y - col.offset_y
