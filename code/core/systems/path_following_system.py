import pygame
from pygame import Vector2
from core.ecs import System
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.animation_sprite import AnimateSprite
from core.managers.entity_manager import EntityManager

class PathFollowingSystem(System):

    def update(self, entity_mn: EntityManager, dt: float):
        for e in entity_mn.get_entities_with(PathFollower, Position, Velocity):
            pf: PathFollower = e.get(PathFollower)
            pos: Position    = e.get(Position)
            vel: Velocity    = e.get(Velocity)

            if self._is_blocked(e, pf):
                vel.vel.update(0, 0)
                pf.done = True
                continue

            self._update_path_progress(pf, pos)
            self._apply_velocity(pf, vel)

            if pf.done and pf.loop:
                pf.restart_path()
                continue
            if e.has(AnimateSprite):
                anim_entity = e  
                anim_entity.set_direction(pf.direction)

    def _is_blocked(self, entity, path_follower: PathFollower) -> bool:
        frozen = entity.get(Freeze).active if entity.has(Freeze) else False
        return frozen or path_follower.done or not path_follower.collision_rects

    def _update_path_progress(self, pf: PathFollower, pos: Position):
        if not pf.collision_rects:
            pf.done, pf.direction = True, Vector2(0, 0)
            return

        target_rect = pf.collision_rects[0]
        center = pos.center_pos()

        if target_rect.collidepoint(center):
            pf.collision_rects.pop(0)
            pf.direction = (
                self._calculate_direction(center, pf.collision_rects[0])
                if pf.collision_rects else Vector2(0, 0)
            )
            pf.done = not bool(pf.collision_rects)

        elif pf.direction.length_squared() == 0:
            pf.direction = self._calculate_direction(center, target_rect)

    def _calculate_direction(self, start_vec: Vector2, target_rect: pygame.Rect) -> Vector2:
        direction = Vector2(target_rect.center) - start_vec
        return direction.normalize() if direction.length_squared() > 0 else Vector2()

    def _apply_velocity(self, pf: PathFollower, vel: Velocity):
        vel.vel = pf.direction * pf.speed
