from core.ecs import Component
class Freeze(Component):
    """Se ativo=True, bloqueia movimentação do NPC (útil durante diálogos)."""
    def __init__(self, active: bool = False):
        self.active = active
