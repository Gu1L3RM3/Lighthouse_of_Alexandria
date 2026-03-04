from core.ecs import Component


class RenderLayer(Component):
    WORLD = 10
    ACTOR = 20
    OVERLAY = 100

    def __init__(self, value: int):
        self.value = int(value)

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "value": self.value,
        }
