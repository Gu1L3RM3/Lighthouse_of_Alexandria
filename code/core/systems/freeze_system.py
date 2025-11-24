from core.ecs import System
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from core.components.freeze import Freeze

class FreezeSystem(System):
    def __init__(self):
        super().__init__()
        self._freeze_requests = 0
        self._is_globally_frozen = False
        self._event_manager = EventManager.get()

    def request_freeze(self, event):
        """Incrementa o contador de solicitações de congelamento."""
        print("Chamou o Freeze")
        print(event['type_request'])
        self._freeze_requests += 1

    def release_freeze(self, event):
        """Decrementa o contador de solicitações de congelamento."""
        self._freeze_requests = max(0, self._freeze_requests - 1)
        
    def update(self, entity_mn: EntityManager, dt: float):
        """Ativa ou desativa o congelamento em todas as entidades relevantes."""
        should_be_frozen = self._freeze_requests > 0

        if should_be_frozen == self._is_globally_frozen:
            return

        self._is_globally_frozen = should_be_frozen
        
        freezable_entities = entity_mn.get_entities_with(Freeze)
        
        for entity in freezable_entities:
            freeze_component: Freeze = entity.get(Freeze)
            freeze_component.active = self._is_globally_frozen
