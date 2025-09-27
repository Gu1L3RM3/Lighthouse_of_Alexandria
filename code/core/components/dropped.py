from core.ecs import Component

class Dropped(Component):
    def __init__(self):
        super().__init__()
        self.can_dropped=True