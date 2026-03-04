from core.ecs import Component


class DynamicCollision(Component):
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "enabled": self.enabled,
        }
