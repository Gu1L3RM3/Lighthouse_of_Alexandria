from core.ecs import Component


class DepthAnchor(Component):
    def __init__(self, offset_y: int = 0):
        self.offset_y = int(offset_y)

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "offset_y": self.offset_y,
        }
