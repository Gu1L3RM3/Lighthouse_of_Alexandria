from core.circuit_tools.serialization_manager import SerializationManager

class StorageCircuitManager:
    def __init__(self):
        self.storage_circuit = SerializationManager.load_eletric_storage()
        self.old_storage_circuit = self.storage_circuit.copy()
        self.revision = 0  # contador de atualizações
    def reload_storage(self):
        self.storage_circuit =  SerializationManager.load_eletric_storage()
    def add_component(self, type: str, value: str):
        self.storage_circuit.setdefault(type, {})
        self.storage_circuit[type].setdefault(value, 0)

        self.storage_circuit[type][value] += 1
        self.revision += 1


    def set_completly_storage(self):
        self.storage_circuit = self.old_storage_circuit.copy()
        self.revision += 1

    def remove_component(self, type: str, value: str):
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
        SerializationManager.save_eletric_storage(self.storage_circuit)
