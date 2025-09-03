from core.ecs import Component
class Freeze(Component):
    def __init__(self, active: bool = False):
        self.active = active
