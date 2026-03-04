from core.ecs import Component


class Team(Component):
    def __init__(self, name: str):
        self.name = name

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "name": self.name,
        }
