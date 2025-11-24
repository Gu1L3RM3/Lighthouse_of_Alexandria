from core.ecs import Component

class EletronTag(Component):
    def __init__(self):
        super().__init__()
    
    def to_dict(self):
        return {}