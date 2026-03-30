from pygame import Vector2

from core.ecs import System, Entity
from core.components.path_follower import PathFollower
from core.components.phantom_ai import PhantomAI
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.map.tile_map import TileMap
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from core.managers.time_manager import TimeManager
from core.settings import PHANTOM_AI_STEALTH_TIMER_NAME


class PhantomAISystem(System):
    STEALTH_TIMER_NAME = PHANTOM_AI_STEALTH_TIMER_NAME

    def __init__(self, tile_map: TileMap):
        self.tile_map = tile_map
        self.event_manager = EventManager.get()
        self.time_manager = TimeManager()
        self.stealth_active = False
        self.stealth_total_duration = 0.0
        self.cancel_reaggro = False
        self._cancel_active_chases_requested = False
        self.chasing_before_stealth: set[int] = set()
        self._stealth_just_ended = False
        self._touch_triggered = False

    def set_touch_triggered(self, value: bool):
        self._touch_triggered = value

    def on_crystal_collected(self, event: dict):
        duration = float(event.get("duration", 6.0))
        if duration <= 0:
            return

        remaining = self.time_manager.remaining(self.STEALTH_TIMER_NAME) if self.stealth_active else 0.0
        self.stealth_active = True
        self.cancel_reaggro = False
        self.stealth_total_duration = remaining + duration
        self.time_manager.set(self.STEALTH_TIMER_NAME, self.stealth_total_duration)

    def on_flask_collected(self, event: dict):
        _ = event
        # Cancela as perseguicoes atuais e exige reentrada na area
        # para que cada fantasma volte a perseguir.
        self.cancel_reaggro = True
        self._cancel_active_chases_requested = True

    def update(self, entity_mn: EntityManager, dt: float):
        _ = dt
        player = entity_mn.get_player()
        if not player or not player.has(Position):
            return
        if player.has(Freeze) and player.get(Freeze).active:
            return

        player_pos: Position = player.get(Position)
        player_center = player_pos.center_pos()

        if self.stealth_active and self.time_manager.ready(self.STEALTH_TIMER_NAME):
            self.stealth_active = False
            self.stealth_total_duration = 0.0
            self._stealth_just_ended = True
            self.event_manager.post({"type": "player_invisible_to_enemies_ended"})
        else:
            self._stealth_just_ended = False

        phantoms = entity_mn.get_entities_with(PhantomAI, Position, Velocity)
        if self._cancel_active_chases_requested:
            self._cancel_active_chases_until_reenter(phantoms)
            self._cancel_active_chases_requested = False

        if self.stealth_active:
            self._force_return_all(phantoms)
        elif self._stealth_just_ended:
            self._on_stealth_end(phantoms)

        for phantom in phantoms:
            ai: PhantomAI = phantom.get(PhantomAI)
            pos: Position = phantom.get(Position)
            vel: Velocity = phantom.get(Velocity)
            self._clamp_inside_map(pos, vel)
            enemy_center = pos.center_pos()

            if self._player_touched(enemy_center, player_center, ai.touch_radius) and not self._touch_triggered:
                self._touch_triggered = True
                self.event_manager.post({"type": "player_touched_enemy"})

            if self.stealth_active:
                ai.was_player_in_range = False
                continue

            in_range = (enemy_center - player_center).length_squared() <= ai.detection_radius * ai.detection_radius
            entering_range = in_range and not ai.was_player_in_range
            exiting_range = (not in_range) and ai.was_player_in_range

            if exiting_range and ai.wait_for_reenter:
                ai.wait_for_reenter = False

            if entering_range and not ai.wait_for_reenter and ai.state != PhantomAI.STATE_CHASE:
                self._start_chase(phantom, ai)

            if ai.state == PhantomAI.STATE_CHASE:
                self._chase_player(phantom, ai, player_center)
            elif ai.state == PhantomAI.STATE_RETURN:
                self._update_return_state(phantom, ai)
            elif ai.state == PhantomAI.STATE_PATROL:
                self._ensure_patrol(phantom, ai, vel)

            ai.was_player_in_range = in_range

    def _player_touched(self, enemy_center: Vector2, player_center: Vector2, touch_radius: float) -> bool:
        return (enemy_center - player_center).length_squared() <= touch_radius * touch_radius

    def _force_return_all(self, phantoms: list[Entity]):
        for phantom in phantoms:
            ai: PhantomAI = phantom.get(PhantomAI)
            if ai.state == PhantomAI.STATE_CHASE:
                self.chasing_before_stealth.add(phantom.id)
                self._set_return_state(phantom, ai)

    def _cancel_active_chases_until_reenter(self, phantoms: list[Entity]):
        for phantom in phantoms:
            ai: PhantomAI = phantom.get(PhantomAI)
            if ai.state != PhantomAI.STATE_CHASE:
                continue
            ai.wait_for_reenter = True
            self._set_return_state(phantom, ai)

    def _on_stealth_end(self, phantoms: list[Entity]):
        if self.cancel_reaggro:
            for phantom in phantoms:
                ai: PhantomAI = phantom.get(PhantomAI)
                if phantom.id in self.chasing_before_stealth:
                    ai.wait_for_reenter = True
            self.chasing_before_stealth.clear()
            self.cancel_reaggro = False
            return

        for phantom in phantoms:
            ai: PhantomAI = phantom.get(PhantomAI)
            if phantom.id in self.chasing_before_stealth:
                self._start_chase(phantom, ai)
        self.chasing_before_stealth.clear()

    def _chase_player(self, phantom: Entity, ai: PhantomAI, player_center: Vector2):
        if phantom.has(PathFollower):
            phantom.remove(PathFollower)
        pos: Position = phantom.get(Position)
        vel: Velocity = phantom.get(Velocity)
        direction = player_center - pos.center_pos()
        if direction.length_squared() == 0:
            vel.vel.update(0, 0)
            return
        direction = direction.normalize()
        vel.vel = direction * ai.chase_speed
        if hasattr(phantom, "set_direction"):
            phantom.set_direction(direction)

    def _set_return_state(self, phantom: Entity, ai: PhantomAI):
        ai.state = PhantomAI.STATE_RETURN
        self._set_return_path(phantom, ai)

    def _set_return_path(self, phantom: Entity, ai: PhantomAI):
        vel: Velocity = phantom.get(Velocity)
        vel.vel.update(0, 0)
        if not ai.route or len(ai.route) < 2:
            ai.state = PhantomAI.STATE_PATROL
            return
        pos: Position = phantom.get(Position)
        start_tile = self.tile_map.get_tile_from_position(pos)
        target_tile = self._nearest_tile(start_tile, ai.route)
        if target_tile is None:
            ai.state = PhantomAI.STATE_PATROL
            return
        return_path = self.tile_map.pathfinder.find_path(start_tile, target_tile)
        if not return_path or len(return_path) < 2:
            # Fallback robusto: retoma patrulha pela rota sem manter velocidade antiga.
            ai.state = PhantomAI.STATE_PATROL
            if phantom.has(PathFollower):
                pf: PathFollower = phantom.get(PathFollower)
                pf.speed = ai.patrol_speed
                pf.loop = True
                pf.set_path(ai.route)
            else:
                phantom.add(PathFollower(ai.route, speed=ai.patrol_speed, loop=True))
            return
        if phantom.has(PathFollower):
            pf: PathFollower = phantom.get(PathFollower)
            pf.speed = ai.patrol_speed
            pf.loop = False
            pf.set_path(return_path)
            return
        phantom.add(PathFollower(return_path, speed=ai.patrol_speed, loop=False))

    def _update_return_state(self, phantom: Entity, ai: PhantomAI):
        if phantom.has(PathFollower):
            pf: PathFollower = phantom.get(PathFollower)
            if not pf.done:
                return
            phantom.remove(PathFollower)
        ai.state = PhantomAI.STATE_PATROL
        self._ensure_patrol(phantom, ai, phantom.get(Velocity))

    def _ensure_patrol(self, phantom: Entity, ai: PhantomAI, vel: Velocity):
        vel.vel.update(0, 0)
        if not ai.route or len(ai.route) < 2:
            return
        if phantom.has(PathFollower):
            pf: PathFollower = phantom.get(PathFollower)
            pf.speed = ai.patrol_speed
            pf.loop = True
            if pf.done:
                pf.restart_path()
            return
        phantom.add(PathFollower(ai.route, speed=ai.patrol_speed, loop=True))

    def _start_chase(self, phantom: Entity, ai: PhantomAI):
        ai.state = PhantomAI.STATE_CHASE
        if phantom.has(PathFollower):
            phantom.remove(PathFollower)

    def _nearest_tile(self, start_tile: tuple[int, int], route: list[tuple[int, int]]) -> tuple[int, int] | None:
        if not route:
            return None
        best_tile = route[0]
        best_dist = self._tile_dist_sq(start_tile, best_tile)
        for tile in route[1:]:
            dist = self._tile_dist_sq(start_tile, tile)
            if dist < best_dist:
                best_dist = dist
                best_tile = tile
        return best_tile

    def _tile_dist_sq(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return dx * dx + dy * dy

    def _clamp_inside_map(self, pos: Position, vel: Velocity):
        max_x = max(0.0, float(self.tile_map.map_width - self.tile_map.tile_width))
        max_y = max(0.0, float(self.tile_map.map_height - self.tile_map.tile_height))
        clamped_x = min(max(pos.x, 0.0), max_x)
        clamped_y = min(max(pos.y, 0.0), max_y)
        if clamped_x != pos.x:
            pos.x = clamped_x
            vel.vx = 0
        if clamped_y != pos.y:
            pos.y = clamped_y
            vel.vy = 0

    def get_stealth_remaining(self) -> float:
        if not self.stealth_active:
            return 0.0
        return self.time_manager.remaining(self.STEALTH_TIMER_NAME)

    def get_stealth_ratio(self) -> float:
        if not self.stealth_active or self.stealth_total_duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.get_stealth_remaining() / self.stealth_total_duration))
