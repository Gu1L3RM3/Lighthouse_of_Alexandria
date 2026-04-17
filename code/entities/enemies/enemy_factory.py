from entities.enemies.spider_enemy import SpiderEnemy
from entities.enemies.phantom_enemy import PhantomEnemy
from core.settings import (
    SPIDER_STANDARD_SPEED,
    SPIDER_WEB_AMBUSH_COOLDOWN_SECONDS,
    SPIDER_WEB_AMBUSH_DURATION_SECONDS,
    SPIDER_WEB_AMBUSH_PREDICTION_SECONDS,
    SPIDER_WEB_AMBUSH_SPEED,
    SPIDER_WEB_ENABLED_DEFAULT,
    SPIDER_WEB_LIFETIME_SECONDS,
    SPIDER_WEB_MAX_PER_SPIDER,
    SPIDER_WEB_MIN_SPAWN_DISTANCE,
    SPIDER_WEB_RADIUS,
    SPIDER_WEB_SLOW_DURATION_SECONDS,
    SPIDER_WEB_SLOW_MULTIPLIER,
    SPIDER_WEB_SPAWN_INTERVAL_SECONDS,
)


class EnemyFactory:
    _registry: dict[str, type] = {
        "spider": SpiderEnemy,
        "phantom": PhantomEnemy,
    }

    @classmethod
    def register(cls, enemy_type: str, enemy_class: type):
        cls._registry[enemy_type.lower()] = enemy_class

    @classmethod
    def create(
        cls,
        enemy_type: str,
        x: float,
        y: float,
        props: dict | None = None,
        route: list[tuple[int, int]] | None = None,
    ):
        key = (enemy_type or "spider").lower()
        enemy_class = cls._registry.get(key)
        if enemy_class is None:
            enemy_class = cls._registry["spider"]

        props = props or {}
        speed = float(props.get("speed", 42))
        if key == "spider":
            # Padroniza velocidade de aranha em todas as fases.
            speed = float(SPIDER_STANDARD_SPEED)
        kwargs = {
            "x": x,
            "y": y,
            "speed": speed,
            "route": route,
        }
        if key == "phantom":
            kwargs["max_hp"] = float(props.get("hp", props.get("max_hp", 130)))
        else:
            kwargs["max_hp"] = float(props.get("hp", props.get("max_hp", 80)))
        if key == "phantom":
            kwargs["detection_radius"] = float(props.get("detection_radius", 90))
            kwargs["touch_radius"] = float(props.get("touch_radius", 10))
            kwargs["chase_speed"] = float(props.get("chase_speed", max(speed, 58)))
        if key == "spider":
            kwargs["web_enabled"] = bool(props.get("web_enabled", SPIDER_WEB_ENABLED_DEFAULT))
            kwargs["web_spawn_interval"] = float(props.get("web_spawn_interval", SPIDER_WEB_SPAWN_INTERVAL_SECONDS))
            kwargs["web_lifetime"] = float(props.get("web_lifetime", SPIDER_WEB_LIFETIME_SECONDS))
            legacy_line_length = float(props.get("web_line_length", SPIDER_WEB_RADIUS * 2.0))
            kwargs["web_radius"] = float(props.get("web_radius", legacy_line_length * 0.5))
            kwargs["max_webs"] = int(props.get("max_webs", SPIDER_WEB_MAX_PER_SPIDER))
            kwargs["min_spawn_distance"] = float(props.get("min_spawn_distance", SPIDER_WEB_MIN_SPAWN_DISTANCE))
            kwargs["web_slow_multiplier"] = float(props.get("web_slow_multiplier", SPIDER_WEB_SLOW_MULTIPLIER))
            kwargs["web_slow_duration"] = float(props.get("web_slow_duration", SPIDER_WEB_SLOW_DURATION_SECONDS))
            kwargs["ambush_speed"] = float(props.get("ambush_speed", max(speed * 1.7, SPIDER_WEB_AMBUSH_SPEED)))
            kwargs["ambush_duration"] = float(props.get("ambush_duration", SPIDER_WEB_AMBUSH_DURATION_SECONDS))
            kwargs["ambush_cooldown"] = float(props.get("ambush_cooldown", SPIDER_WEB_AMBUSH_COOLDOWN_SECONDS))
            kwargs["ambush_prediction_seconds"] = float(props.get("ambush_prediction_seconds", SPIDER_WEB_AMBUSH_PREDICTION_SECONDS))
        return enemy_class(**kwargs)
