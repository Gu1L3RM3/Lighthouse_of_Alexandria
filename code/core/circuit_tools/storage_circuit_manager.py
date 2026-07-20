from copy import deepcopy

from core.circuit_tools.serialization_manager import SerializationManager


class StorageCircuitManager:
    def __init__(self):
        self.storage_circuit = SerializationManager.load_eletric_storage()
        self.old_storage_circuit = deepcopy(self.storage_circuit)
        self.revision = 0  # contador de atualizacoes
        self._listeners = []

    def add_listener(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def _mark_changed(self):
        self.revision += 1
        for listener in tuple(getattr(self, "_listeners", ())):
            listener()

    def sync_baseline(self):
        self.old_storage_circuit = deepcopy(self.storage_circuit)

    def reload_storage(self):
        self.storage_circuit = SerializationManager.load_eletric_storage()
        self._mark_changed()

    def add_component(self, type: str, value: str, quantity: int = 1):
        quantity = int(quantity)
        if quantity <= 0:
            return False
        self.storage_circuit.setdefault(type, {})
        self.storage_circuit[type].setdefault(value, 0)
        self.storage_circuit[type][value] += quantity
        self._mark_changed()
        return True

    def set_completly_storage(self):
        self.storage_circuit = deepcopy(self.old_storage_circuit)
        self._mark_changed()

    def remove_component(self, type: str, value: str, quantity: int = 1):
        quantity = int(quantity)
        if quantity <= 0:
            return False
        if type not in self.storage_circuit:
            return False
        if value not in self.storage_circuit[type]:
            return False
        if self.storage_circuit[type][value] < quantity:
            return False

        self.storage_circuit[type][value] -= quantity
        self._mark_changed()
        return True

    def component_count(self, type: str, value: str) -> int:
        return max(0, int(self.storage_circuit.get(type, {}).get(value, 0)))

    def remove_all_components(self):
        for comp_type in self.storage_circuit:
            self.storage_circuit[comp_type].clear()
        self._mark_changed()

    def save_eletric_storage(self):
        SerializationManager.save_eletric_storage(self.storage_circuit)
