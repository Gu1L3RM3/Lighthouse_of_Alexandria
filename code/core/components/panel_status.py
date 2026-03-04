from core.ecs import Component


class PanelStatus(Component):
    def __init__(self, is_active: bool = True, is_done: bool = False):
        self.is_active = bool(is_active)
        self.is_done = bool(is_done)

    @property
    def state(self) -> str:
        if not self.is_active:
            return "inactive"
        if self.is_done:
            return "done"
        return "pending"

    def set_active(self, value: bool):
        self.is_active = bool(value)

    def set_done(self, value: bool):
        self.is_done = bool(value)

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "is_active": self.is_active,
            "is_done": self.is_done,
            "state": self.state,
        }
