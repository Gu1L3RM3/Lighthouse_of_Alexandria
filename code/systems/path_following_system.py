import pygame
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze

class PathFollowingSystem:
    """
    Define a VELOCIDADE de entidades com PathFollower para que se movam
    em direção ao próximo nó do caminho. Delega o movimento e colisão ao PhysicsSystem.
    """
    def __init__(self, navgrid):
        self.g = navgrid
        self.slowing_radius = self.g.tile_width * 2

    def update(self, entities, dt: float):
        for e in entities:
            
            pf = e.get(PathFollower)
            if not pf or not e.has(Position):
                continue

            # Adiciona Velocity se não existir
            if not e.has(Velocity):
                e.add(Velocity())
            vel: Velocity = e.get(Velocity)

            # Se a entidade estiver congelada, zera a velocidade e para
            if e.has(Freeze) and e.get(Freeze).active:
                vel.vel.update(0, 0)
                continue

            pos: Position = e.get(Position)
            
            # Se o caminho terminou, zera a velocidade e remove o PathFollower
            if pf.done or pf.current_index >= len(pf.path_tiles):
                pf.done = True
                vel.vel.update(0, 0)
                e.remove(PathFollower)
                continue
            
            target_tile = pf.path_tiles[pf.current_index]
            target_pos = pygame.Vector2(self.g.pixel_center(*target_tile))
            
            entity_center_pos = pygame.Vector2(pos.x + self.g.tile_width / 2, pos.y + self.g.tile_height / 2)
            direction_vec = target_pos - entity_center_pos
            dist = direction_vec.length()

            if dist < self.g.tile_width / 2:
                pf.current_index += 1
                continue

            if dist > 0:
                direction_vec.normalize_ip()

            is_last_node = (pf.current_index == len(pf.path_tiles) - 1)
            if is_last_node and dist < self.slowing_radius:
                mapped_speed = pf.speed * (dist / self.slowing_radius)
                vel.vel = direction_vec * mapped_speed
            else:
                vel.vel = direction_vec * pf.speed