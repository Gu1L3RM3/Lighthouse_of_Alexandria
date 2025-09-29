from core.ecs import Component

class Dropped(Component):
    def __init__(self,can_dropped=True):
        super().__init__()
        self.can_dropped=can_dropped
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'can_dropped':self.can_dropped
        }
    @classmethod
    def from_dict(cls, data: dict) -> "Dropped":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
        can_dropped=data['can_dropped']
        return cls(can_dropped)