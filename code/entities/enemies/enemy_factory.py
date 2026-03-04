from entities.enemies.spider_enemy import SpiderEnemy


class EnemyFactory:
    _registry: dict[str, type] = {
        "spider": SpiderEnemy,
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
        return enemy_class(
            x=x,
            y=y,
            speed=speed,
            route=route,
        )
