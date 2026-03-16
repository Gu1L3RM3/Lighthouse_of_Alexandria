from core.ecs import Component


class Health(Component):
    def __init__(self, max_hp: float, current_hp: float | None = None):
        self.max_hp = max(1.0, float(max_hp))
        self.current_hp = self.max_hp if current_hp is None else max(0.0, min(float(current_hp), self.max_hp))

    def take_damage(self, amount: float) -> bool:
        damage = max(0.0, float(amount))
        self.current_hp = max(0.0, self.current_hp - damage)
        return self.current_hp <= 0.0

    def heal_full(self):
        self.current_hp = self.max_hp

    def is_dead(self) -> bool:
        return self.current_hp <= 0.0

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
        }
