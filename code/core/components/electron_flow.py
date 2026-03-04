from core.ecs import Component


class ElectronFlow(Component):
    def __init__(
        self,
        base_speed: float = 90.0,
        min_speed: float = 40.0,
        max_speed: float = 180.0,
        accel_rate: float = 280.0,
        decel_rate: float = 240.0,
        relax_rate: float = 80.0,
        boost_amount: float = 45.0,
        brake_amount: float = 30.0,
    ):
        self.base_speed = base_speed
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.accel_rate = accel_rate
        self.decel_rate = decel_rate
        self.relax_rate = relax_rate
        self.boost_amount = boost_amount
        self.brake_amount = brake_amount

        self.current_speed = base_speed
        self.target_speed = base_speed

    def _clamp(self, value: float) -> float:
        return max(self.min_speed, min(self.max_speed, value))

    def boost(self):
        self.target_speed = self._clamp(self.target_speed + self.boost_amount)
        # Impacto imediato para ficar perceptivel na passagem pela fonte.
        self.current_speed = self._clamp(self.current_speed + (self.boost_amount * 0.7))

    def brake(self):
        self.target_speed = self._clamp(self.target_speed - self.brake_amount)
        # Freio imediato para deixar claro o efeito no resistor.
        self.current_speed = self._clamp(self.current_speed - (self.brake_amount * 0.7))

    def update(self, dt: float):
        if dt <= 0:
            return

        if self.target_speed > self.current_speed:
            self.current_speed = min(self.target_speed, self.current_speed + self.accel_rate * dt)
        elif self.target_speed < self.current_speed:
            self.current_speed = max(self.target_speed, self.current_speed - self.decel_rate * dt)

        if self.target_speed > self.base_speed:
            self.target_speed = max(self.base_speed, self.target_speed - self.relax_rate * dt)
        elif self.target_speed < self.base_speed:
            self.target_speed = min(self.base_speed, self.target_speed + self.relax_rate * dt)

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "base_speed": self.base_speed,
            "current_speed": self.current_speed,
            "target_speed": self.target_speed,
            "min_speed": self.min_speed,
            "max_speed": self.max_speed,
        }
