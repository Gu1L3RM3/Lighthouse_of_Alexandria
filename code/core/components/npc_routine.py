from core.ecs import Component

class NPCRoutine(Component):
    """
    Guarda a rotina por hora -> destino (em NOME de waypoint).
    Ex.: {9: "sala", 14: "patio", 18: "casa"}
    """
    def __init__(self, schedule: dict[int, str]):
        self.schedule = schedule
        self.last_hour_checked = None
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'schedule':self.schedule,
            'last_hour_checked':self.last_hour_checked
        }
