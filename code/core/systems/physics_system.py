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

        # --- Movimento e Colisão no Eixo X ---
        pos.x += vel.vx * dt
        rect = col.get_rect(pos.x, pos.y)

        # Checa colisão com paredes estáticas
        for wall in self.static_colliders:
            if rect.colliderect(wall):
                if vel.vx > 0:  # Movendo para a direita
                    rect.right = wall.left
                elif vel.vx < 0:  # Movendo para a esquerda
                    rect.left = wall.right
                pos.x = rect.x - col.offset_x # Atualiza a posição real da entidade
                vel.vx = 0 # Opcional: para a velocidade para evitar "grudar"
                break # Sai do loop assim que uma colisão é resolvida

        # Checa colisão com outras entidades (se necessário)
        # Nota: Esta parte pode ser complexa dependendo do seu jogo.
        # Por enquanto, focaremos nos colisores estáticos que é a causa principal do jitter.


        # --- Movimento e Colisão no Eixo Y ---
        pos.y += vel.vy * dt
        rect = col.get_rect(pos.x, pos.y) # Pega o rect com a posição X já corrigida

        # Checa colisão com paredes estáticas
        for wall in self.static_colliders:
            if rect.colliderect(wall):
                if vel.vy > 0:  # Movendo para baixo
                    rect.bottom = wall.top
                elif vel.vy < 0:  # Movendo para cima
                    rect.top = wall.bottom
                pos.y = rect.y - col.offset_y # Atualiza a posição real da entidade
                vel.vy = 0 # Opcional
                break