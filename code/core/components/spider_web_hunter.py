from core.ecs import Component


class SpiderWebHunter(Component):
    def __init__(
        self,
        enabled: bool = True,
        web_spawn_interval: float = 3.2,
        web_lifetime: float = 14.0,
        web_radius: float = 14.0,
        max_webs: int = 3,
        min_spawn_distance: float = 28.0,
        slow_multiplier: float = 0.45,
        slow_duration: float = 1.15,
        ambush_speed: float = 128.0,
        ambush_duration: float = 0.55,
        ambush_cooldown: float = 3.0,
        prediction_seconds: float = 0.35,
    ):
        self.enabled = bool(enabled)
        self.web_spawn_interval = max(0.4, float(web_spawn_interval))
        self.web_lifetime = max(1.0, float(web_lifetime))
        self.web_radius = max(6.0, float(web_radius))
        self.max_webs = max(1, int(max_webs))
        self.min_spawn_distance = max(0.0, float(min_spawn_distance))
        self.slow_multiplier = max(0.1, min(1.0, float(slow_multiplier)))
        self.slow_duration = max(0.2, float(slow_duration))
        self.ambush_speed = max(1.0, float(ambush_speed))
        self.ambush_duration = max(0.1, float(ambush_duration))
        self.ambush_cooldown = max(0.0, float(ambush_cooldown))
        self.prediction_seconds = max(0.0, float(prediction_seconds))

        # Runtime state
        self.web_spawn_timer = self.web_spawn_interval
        self.ambush_timer = 0.0
        self.ambush_cooldown_timer = 0.0
        self.ambush_target: tuple[float, float] | None = None
        self.chase_timer = 0.0
        self.web_entity_ids: list[int] = []
        self.last_web_center: tuple[float, float] | None = None

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "enabled": self.enabled,
            "web_spawn_interval": self.web_spawn_interval,
            "web_lifetime": self.web_lifetime,
            "web_radius": self.web_radius,
            "max_webs": self.max_webs,
            "min_spawn_distance": self.min_spawn_distance,
            "slow_multiplier": self.slow_multiplier,
            "slow_duration": self.slow_duration,
            "ambush_speed": self.ambush_speed,
            "ambush_duration": self.ambush_duration,
            "ambush_cooldown": self.ambush_cooldown,
            "prediction_seconds": self.prediction_seconds,
        }
