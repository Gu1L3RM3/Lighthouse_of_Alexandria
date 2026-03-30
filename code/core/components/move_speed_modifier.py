from core.ecs import Component


class MoveSpeedModifier(Component):
    def __init__(self, multiplier: float = 1.0, duration: float = 0.0):
        self.multiplier = max(0.1, min(1.0, float(multiplier)))
        self.duration = max(0.0, float(duration))

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "multiplier": self.multiplier,
            "duration": self.duration,
        }
