from pygame import Vector2

from core.ecs import System, Entity
from core.components.freeze import Freeze
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.move_speed_modifier import MoveSpeedModifier
from core.components.spider_web_hunter import SpiderWebHunter
from core.components.spider_web_trap import SpiderWebTrap
from core.managers.entity_manager import EntityManager
from core.settings import (
    SPIDER_WEB_ALERT_MAX_HELPERS,
    SPIDER_WEB_ALERT_RADIUS,
    SPIDER_WEB_ARM_DELAY_SECONDS,
    SPIDER_WEB_CHASE_MAX_SECONDS,
    SPIDER_WEB_CHASE_MIN_SECONDS,
    SPIDER_WEB_CHASE_TIME_MARGIN_SECONDS,
    SPIDER_WEB_GLOBAL_MAX_ACTIVE,
    SPIDER_WEB_PLAYER_GRACE_SECONDS,
    SPIDER_WEB_RADIUS,
)
from entities.enemies.spider_web_trap_entity import SpiderWebTrapEntity


class SpiderWebSystem(System):
    def __init__(self):
        self._player_web_grace_remaining = 0.0

    def update(self, entity_mn: EntityManager, dt: float):
        player = entity_mn.get_player()
        if not player or not player.has(Position):
            return

        self._player_web_grace_remaining = max(0.0, self._player_web_grace_remaining - dt)
        self._update_player_speed_modifier(player, dt)
        self._update_traps(entity_mn, player, dt)
        self._update_spiders(entity_mn, player, dt)

    def _update_player_speed_modifier(self, player: Entity, dt: float):
        if not player.has(MoveSpeedModifier):
            return
        mod: MoveSpeedModifier = player.get(MoveSpeedModifier)
        mod.duration -= dt
        if mod.duration <= 0:
            player.remove(MoveSpeedModifier)
            return
        if player.has(Velocity):
            vel: Velocity = player.get(Velocity)
            vel.vel *= mod.multiplier

    def _update_traps(self, entity_mn: EntityManager, player: Entity, dt: float):
        traps = entity_mn.get_entities_with(SpiderWebTrap)
        if not traps:
            return

        player_center = player.get(Position).center_pos()
        to_remove: list[int] = []

        for trap_entity in traps:
            trap: SpiderWebTrap = trap_entity.get(SpiderWebTrap)
            trap.lifetime -= dt
            trap.arm_delay = max(0.0, trap.arm_delay - dt)
            if trap.lifetime <= 0:
                to_remove.append(trap_entity.id)
                continue

            if trap.arm_delay > 0 or trap.triggered:
                continue
            if self._player_web_grace_remaining > 0:
                continue

            trap_center = Vector2(trap.center_x, trap.center_y)
            if (trap_center - player_center).length_squared() > (trap.radius * trap.radius):
                continue

            trap.triggered = True
            to_remove.append(trap_entity.id)
            self._apply_slow(player, trap.slow_multiplier, trap.slow_duration)
            self._trigger_spider_chase(entity_mn, trap, player_center, player)
            self._player_web_grace_remaining = max(self._player_web_grace_remaining, SPIDER_WEB_PLAYER_GRACE_SECONDS)

        if not to_remove:
            return

        for entity_id in to_remove:
            trap_entity = entity_mn.get_entity_by_id(entity_id)
            if not trap_entity or not trap_entity.has(SpiderWebTrap):
                continue
            trap: SpiderWebTrap = trap_entity.get(SpiderWebTrap)
            self._unlink_trap_from_owner(entity_mn, trap.owner_id, trap_entity.id)
            entity_mn.remove_entity(trap_entity)

    def _apply_slow(self, player: Entity, multiplier: float, duration: float):
        if player.has(MoveSpeedModifier):
            mod: MoveSpeedModifier = player.get(MoveSpeedModifier)
            mod.multiplier = min(mod.multiplier, multiplier)
            mod.duration = max(mod.duration, duration)
            return
        player.add(MoveSpeedModifier(multiplier=multiplier, duration=duration))

    def _trigger_spider_chase(
        self,
        entity_mn: EntityManager,
        trap: SpiderWebTrap,
        player_center: Vector2,
        player: Entity,
    ):
        trap_center = Vector2(trap.center_x, trap.center_y)
        owner = entity_mn.get_entity_by_id(trap.owner_id)
        if owner and owner.has(SpiderWebHunter):
            self._start_spider_chase(owner, owner.get(SpiderWebHunter), player_center, trap_center, player)

        self._alert_nearby_spiders(entity_mn, trap.owner_id, trap_center, player_center, player)

    def _update_spiders(self, entity_mn: EntityManager, player: Entity, dt: float):
        player_center = player.get(Position).center_pos()
        spiders = entity_mn.get_entities_with(SpiderWebHunter, Position, Velocity)

        for spider in spiders:
            hunter: SpiderWebHunter = spider.get(SpiderWebHunter)
            if not hunter.enabled:
                continue

            hunter.web_spawn_timer -= dt
            hunter.ambush_timer = max(0.0, hunter.ambush_timer - dt)
            hunter.ambush_cooldown_timer = max(0.0, hunter.ambush_cooldown_timer - dt)
            hunter.chase_timer = max(0.0, hunter.chase_timer - dt)
            self._prune_missing_traps(entity_mn, hunter)

            if spider.has(Freeze) and spider.get(Freeze).active:
                continue

            if hunter.chase_timer > 0:
                self._apply_slow_chase_motion(spider, hunter, player_center)
                continue

            if hunter.ambush_timer > 0 and hunter.ambush_target is not None:
                self._apply_ambush_motion(spider, hunter)
                continue

            hunter.ambush_target = None
            self._spawn_trap_if_ready(entity_mn, spider, hunter)

    def _apply_ambush_motion(self, spider: Entity, hunter: SpiderWebHunter):
        pos: Position = spider.get(Position)
        vel: Velocity = spider.get(Velocity)
        target = Vector2(hunter.ambush_target)
        direction = target - pos.center_pos()

        if direction.length_squared() <= 4.0:
            vel.vel.update(0, 0)
            hunter.ambush_timer = 0.0
            return

        direction = direction.normalize()
        vel.vel = direction * hunter.ambush_speed
        if hasattr(spider, "set_direction"):
            spider.set_direction(direction)

    def _start_spider_chase(
        self,
        spider: Entity,
        hunter: SpiderWebHunter,
        player_center: Vector2,
        trap_center: Vector2,
        player: Entity,
    ):
        if not spider.has(Position):
            return
        spider_center = spider.get(Position).center_pos()
        chase_speed = max(1.0, hunter.ambush_speed)
        distance = (spider_center - trap_center).length()
        chase_duration = (distance / chase_speed) + SPIDER_WEB_CHASE_TIME_MARGIN_SECONDS
        chase_duration = max(SPIDER_WEB_CHASE_MIN_SECONDS, min(SPIDER_WEB_CHASE_MAX_SECONDS, chase_duration))

        hunter.chase_timer = max(hunter.chase_timer, chase_duration)
        predicted_center = player_center.copy()
        if player.has(Velocity):
            p_vel: Velocity = player.get(Velocity)
            predicted_center += p_vel.vel * hunter.prediction_seconds
        hunter.ambush_target = (float(predicted_center.x), float(predicted_center.y))
        hunter.ambush_timer = max(hunter.ambush_timer, min(chase_duration, hunter.ambush_duration))
        hunter.ambush_cooldown_timer = max(hunter.ambush_cooldown_timer, hunter.ambush_cooldown)

    def _alert_nearby_spiders(
        self,
        entity_mn: EntityManager,
        owner_id: int,
        trap_center: Vector2,
        player_center: Vector2,
        player: Entity,
    ):
        if SPIDER_WEB_ALERT_MAX_HELPERS <= 0 or SPIDER_WEB_ALERT_RADIUS <= 0:
            return
        radius_sq = SPIDER_WEB_ALERT_RADIUS * SPIDER_WEB_ALERT_RADIUS
        candidates: list[tuple[float, Entity, SpiderWebHunter]] = []

        for spider in entity_mn.get_entities_with(SpiderWebHunter, Position):
            if spider.id == owner_id:
                continue
            hunter: SpiderWebHunter = spider.get(SpiderWebHunter)
            if not hunter.enabled:
                continue
            spider_center = spider.get(Position).center_pos()
            dist_sq = (spider_center - trap_center).length_squared()
            if dist_sq > radius_sq:
                continue
            candidates.append((dist_sq, spider, hunter))

        candidates.sort(key=lambda item: item[0])
        for _, spider, hunter in candidates[:SPIDER_WEB_ALERT_MAX_HELPERS]:
            self._start_spider_chase(spider, hunter, player_center, trap_center, player)

    def _apply_slow_chase_motion(self, spider: Entity, hunter: SpiderWebHunter, player_center: Vector2):
        pos: Position = spider.get(Position)
        vel: Velocity = spider.get(Velocity)
        direction = player_center - pos.center_pos()
        if direction.length_squared() <= 4.0:
            vel.vel.update(0, 0)
            return
        direction = direction.normalize()
        vel.vel = direction * hunter.ambush_speed
        if hasattr(spider, "set_direction"):
            spider.set_direction(direction)

    def _spawn_trap_if_ready(self, entity_mn: EntityManager, spider: Entity, hunter: SpiderWebHunter):
        if hunter.web_spawn_timer > 0:
            return
        if self._active_trap_count(entity_mn) >= SPIDER_WEB_GLOBAL_MAX_ACTIVE:
            hunter.web_spawn_timer = min(hunter.web_spawn_interval, 0.9)
            return
        if len(hunter.web_entity_ids) >= hunter.max_webs:
            hunter.web_spawn_timer = min(hunter.web_spawn_interval, 0.75)
            return
        if spider.has(PathFollower):
            pf: PathFollower = spider.get(PathFollower)
            if pf.done:
                hunter.web_spawn_timer = 0.3
                return

        center = spider.get(Position).center_pos()
        if hunter.last_web_center is not None:
            last_center = Vector2(hunter.last_web_center)
            if (center - last_center).length_squared() < (hunter.min_spawn_distance * hunter.min_spawn_distance):
                hunter.web_spawn_timer = 0.35
                return

        trap = SpiderWebTrapEntity(
            owner_id=spider.id,
            center_x=center.x,
            center_y=center.y,
            radius=float(getattr(hunter, "web_radius", SPIDER_WEB_RADIUS)),
            lifetime=hunter.web_lifetime,
            slow_multiplier=hunter.slow_multiplier,
            slow_duration=hunter.slow_duration,
            arm_delay=SPIDER_WEB_ARM_DELAY_SECONDS,
        )
        entity_mn.add_entity(trap)
        hunter.web_entity_ids.append(trap.id)
        hunter.last_web_center = (float(center.x), float(center.y))
        hunter.web_spawn_timer = hunter.web_spawn_interval

    def destroy_traps_in_radius(self, entity_mn: EntityManager, center: Vector2, radius: float) -> int:
        if radius <= 0:
            return 0
        removed = 0
        traps = entity_mn.get_entities_with(SpiderWebTrap)
        for trap_entity in traps:
            trap: SpiderWebTrap = trap_entity.get(SpiderWebTrap)
            trap_center = Vector2(trap.center_x, trap.center_y)
            if (trap_center - center).length_squared() > (radius * radius):
                continue
            self._unlink_trap_from_owner(entity_mn, trap.owner_id, trap_entity.id)
            entity_mn.remove_entity(trap_entity)
            removed += 1
        return removed

    def _unlink_trap_from_owner(self, entity_mn: EntityManager, owner_id: int, trap_id: int):
        owner = entity_mn.get_entity_by_id(owner_id)
        if not owner or not owner.has(SpiderWebHunter):
            return
        hunter: SpiderWebHunter = owner.get(SpiderWebHunter)
        if trap_id in hunter.web_entity_ids:
            hunter.web_entity_ids.remove(trap_id)

    def _prune_missing_traps(self, entity_mn: EntityManager, hunter: SpiderWebHunter):
        if not hunter.web_entity_ids:
            return
        alive_ids = []
        for trap_id in hunter.web_entity_ids:
            trap_entity = entity_mn.get_entity_by_id(trap_id)
            if trap_entity and trap_entity.has(SpiderWebTrap):
                alive_ids.append(trap_id)
        hunter.web_entity_ids = alive_ids

    def _active_trap_count(self, entity_mn: EntityManager) -> int:
        return len(entity_mn.get_entities_with(SpiderWebTrap))
