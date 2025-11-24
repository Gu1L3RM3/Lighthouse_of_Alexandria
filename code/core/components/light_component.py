from core.ecs import Component

class LightComponent(Component):
    def __init__(self,light_on=True,radius=25):
        super().__init__()
        self.light_on = light_on
        self.radius   = radius
    def to_dict(self):
        pass