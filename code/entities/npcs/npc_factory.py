from entities.npcs.npc_guard import GuardNPC
from entities.npcs.npc_professor import ProfessorNPC

class NPCFactory:
    registry = {
        "guard": GuardNPC,
        "professor": ProfessorNPC,
    }

    @classmethod
    def create(cls, npc_type: str, x: int, y: int, props: dict):
        npc_class = cls.registry.get(npc_type.lower())
        if npc_class:
            return npc_class(x, y, props)
        raise ValueError(f"NPC type '{npc_type}' not registered")
