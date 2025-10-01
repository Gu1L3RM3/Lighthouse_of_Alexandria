from core.ecs import Component
class Connectable(Component):
    def __init__(self, base_connections: set[str]):
        super().__init__()
        self.base_connections = base_connections
    def set_connections(self, angle_deg: int):
        normalized = angle_deg % 360
        mapping = {
            0:   {"top": "top", "bottom": "bottom", "left": "left", "right": "right"},
            90:  {"top": "left", "bottom": "right", "left": "bottom", "right": "top"},
            180: {"top": "bottom", "bottom": "top", "left": "right", "right": "left"},
            270: {"top": "left", "bottom": "right", "left": "bottom", "right": "top"},
        }
        table = mapping.get(normalized, mapping[0])

        rotated = set()
        for c in self.base_connections:
            if c in table:
                rotated.add(table[c])

        self.base_connections = rotated
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'connections':list(self.base_connections)
        }
    @classmethod
    def from_dict(cls, data: dict) -> "Connectable":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
            
        base_connections = set(data['connections'])
        return cls(base_connections=base_connections)