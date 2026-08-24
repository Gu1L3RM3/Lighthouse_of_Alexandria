from copy import deepcopy

from core.circuit_tools.inventory_repository import InventoryRepository


class StorageCircuitManager:
    def __init__(self, repository: InventoryRepository | None = None):
        self.repository = repository or InventoryRepository()
        self.storage_circuit = self.repository.load()
        self.old_storage_circuit = deepcopy(self.storage_circuit)
        self.revision = 0  # contador de atualizacoes

    def sync_baseline(self):
        self.old_storage_circuit = deepcopy(self.storage_circuit)

    def reload_storage(self):
        self.storage_circuit = self.repository.load()

    def add_component(self, type: str, value: str):
        self.storage_circuit.setdefault(type, {})
        self.storage_circuit[type].setdefault(value, 0)
        self.storage_circuit[type][value] += 1
        self.revision += 1

    def set_completly_storage(self):
        self.storage_circuit = deepcopy(self.old_storage_circuit)
        self.revision += 1

    def remove_component(self, type: str, value: str):
        if type not in self.storage_circuit:
            return False
        if value not in self.storage_circuit[type]:
            return False
        if self.storage_circuit[type][value] == 0:
            return False

        self.storage_circuit[type][value] -= 1
        self.revision += 1
        return self.storage_circuit[type][value] != 0

    def remove_all_components(self):
        for comp_type in self.storage_circuit:
            self.storage_circuit[comp_type].clear()
        self.revision += 1

    def save_eletric_storage(self):
        self.repository.save(self.storage_circuit)
