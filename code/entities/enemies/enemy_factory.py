from entities.enemies.spider_enemy import SpiderEnemy
from entities.enemies.phantom_enemy import PhantomEnemy


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
        return enemy_class(**kwargs)
