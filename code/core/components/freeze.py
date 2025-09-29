from core.ecs import Component
class Freeze(Component):
    def __init__(self, active: bool = False):
        self.active = active
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'active':self.active
        }
