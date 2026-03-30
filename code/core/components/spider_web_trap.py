from core.ecs import Component


class SpiderWebTrap(Component):
    def __init__(
        self,
        owner_id: int,
        center_x: float,
        center_y: float,
        radius: float = 14.0,
        lifetime: float = 14.0,
        slow_multiplier: float = 0.45,
        slow_duration: float = 1.15,
        arm_delay: float = 0.1,
    ):
        self.owner_id = int(owner_id)
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.radius = max(4.0, float(radius))
        self.lifetime = max(0.1, float(lifetime))
        self.slow_multiplier = max(0.1, min(1.0, float(slow_multiplier)))
        self.slow_duration = max(0.1, float(slow_duration))
        self.arm_delay = max(0.0, float(arm_delay))
        self.triggered = False

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "owner_id": self.owner_id,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "radius": self.radius,
            "lifetime": self.lifetime,
            "slow_multiplier": self.slow_multiplier,
            "slow_duration": self.slow_duration,
            "arm_delay": self.arm_delay,
            "triggered": self.triggered,
        }
