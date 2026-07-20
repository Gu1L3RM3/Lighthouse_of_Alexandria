import unittest

from core.circuit_tools.component_inventory_service import ComponentInventoryService
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from scenes.fases.component_overload_service import ComponentOverloadService
from core.components.position import Position
from core.ecs import Entity
from core.managers.event_manager import EventManager
from core.systems.circuit_editor.input_system import InputSystem
from entities.itens.resistor_item import ResistorItem
from entities.player import Player


class _MemoryStorage:
    def __init__(self, data=None):
        self.storage_circuit = data or {}
        self.revision = 0

    def add_component(self, type: str, value: str, quantity: int = 1):
        values = self.storage_circuit.setdefault(type, {})
        values[value] = values.get(value, 0) + quantity
        self.revision += 1
        return True

    def remove_component(self, type: str, value: str, quantity: int = 1):
        available = self.storage_circuit.get(type, {}).get(value, 0)
        if available < quantity:
            return False
        self.storage_circuit[type][value] = available - quantity
        self.revision += 1
        return True


class ComponentInventoryServiceTests(unittest.TestCase):
    def make_service(self, data=None, capacity=6.0):
        storage = _MemoryStorage(data)
        service = ComponentInventoryService(storage, max_weight_provider=lambda: capacity)
        return storage, service

    def test_weight_is_derived_from_type_and_quantity(self):
        _, service = self.make_service(
            {
                "Resistor": {"10": 2},
                "CurrentSource": {"0.1": 1},
                "VoutageSource": {"5": 1},
            },
            capacity=10,
        )

        self.assertEqual(service.current_weight, 7.0)

    def test_accepts_a_component_that_exactly_fills_capacity(self):
        storage, service = self.make_service({"Resistor": {"10": 1}}, capacity=2.0)

        accepted = service.try_add("Resistor", "20")

        self.assertTrue(accepted)
        self.assertEqual(service.current_weight, 2.0)
        self.assertEqual(storage.storage_circuit["Resistor"]["20"], 1)
        self.assertTrue(service.is_full)

    def test_rejects_component_that_would_exceed_capacity_without_mutating_storage(self):
        storage, service = self.make_service({"CurrentSource": {"0.1": 1}}, capacity=3.0)

        accepted = service.try_add("Resistor", "10")

        self.assertFalse(accepted)
        self.assertNotIn("Resistor", storage.storage_circuit)
        self.assertEqual(service.current_weight, 2.5)

    def test_take_many_is_atomic_when_components_do_not_fit(self):
        storage, service = self.make_service({"Resistor": {"10": 1}}, capacity=3.0)

        accepted = service.try_add_many(
            [
                ("Resistor", "20", 1),
                ("CurrentSource", "0.1", 1),
            ]
        )

        self.assertFalse(accepted)
        self.assertEqual(storage.storage_circuit, {"Resistor": {"10": 1}})

    def test_placing_component_removes_it_and_reduces_weight(self):
        storage, service = self.make_service({"VoutageSource": {"5": 1}}, capacity=4.0)

        removed = service.try_remove("VoutageSource", "5")

        self.assertTrue(removed)
        self.assertEqual(service.current_weight, 0.0)
        self.assertEqual(storage.storage_circuit["VoutageSource"]["5"], 0)

    def test_normalizes_legacy_voltage_source_names(self):
        _, service = self.make_service({"VoltageSource": {"5": 1}}, capacity=3.0)

        self.assertEqual(service.current_weight, 2.5)


class StorageCircuitManagerContractTests(unittest.TestCase):
    def make_storage(self, data):
        storage = StorageCircuitManager.__new__(StorageCircuitManager)
        storage.storage_circuit = data
        storage.old_storage_circuit = {}
        storage.revision = 0
        return storage

    def test_remove_component_returns_operation_success_even_when_last_item_was_removed(self):
        storage = self.make_storage({"Resistor": {"10": 1}})

        removed = storage.remove_component("Resistor", "10")

        self.assertTrue(removed)
        self.assertEqual(storage.storage_circuit["Resistor"]["10"], 0)

    def test_remove_component_does_not_mutate_when_quantity_is_unavailable(self):
        storage = self.make_storage({"Resistor": {"10": 1}})

        removed = storage.remove_component("Resistor", "10", quantity=2)

        self.assertFalse(removed)
        self.assertEqual(storage.storage_circuit["Resistor"]["10"], 1)
        self.assertEqual(storage.revision, 0)


class _InventorySnapshot:
    def __init__(self, weight=0.0, capacity=4.0):
        self.current_weight = weight
        self.max_weight = capacity
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def change_weight(self, weight):
        self.current_weight = weight
        for listener in self._listeners:
            listener()


class ComponentOverloadIntegrationTests(unittest.TestCase):
    def test_inventory_change_recomputes_bar_and_speed(self):
        applied = []
        inventory = _InventorySnapshot(weight=0.0, capacity=4.0)
        overload = ComponentOverloadService(
            speed_multiplier_applier=applied.append,
            inventory_service=inventory,
        )

        inventory.change_weight(4.0)

        snapshot = overload.get_snapshot()
        self.assertEqual(snapshot["weight"], 4.0)
        self.assertEqual(snapshot["ratio"], 1.0)
        self.assertEqual(applied[-1], 0.74)

    def test_solving_panel_does_not_reduce_weight_without_inventory_transfer(self):
        inventory = _InventorySnapshot(weight=2.5, capacity=4.0)
        overload = ComponentOverloadService(
            speed_multiplier_applier=lambda _: None,
            inventory_service=inventory,
        )

        overload.on_panel_solved({"area_id": 1})

        self.assertEqual(overload.get_snapshot()["weight"], 2.5)

    def test_direct_storage_reset_also_recomputes_weight(self):
        storage = StorageCircuitManager.__new__(StorageCircuitManager)
        storage.storage_circuit = {"Resistor": {"10": 2}}
        storage.old_storage_circuit = {}
        storage.revision = 0
        storage._listeners = []
        inventory = ComponentInventoryService(storage, max_weight_provider=lambda: 4.0)
        overload = ComponentOverloadService(
            speed_multiplier_applier=lambda _: None,
            inventory_service=inventory,
        )

        storage.remove_all_components()

        self.assertEqual(overload.get_snapshot()["weight"], 0.0)


class _EditorEntityManager:
    def __init__(self, entities):
        self.entities = list(entities)
        self.removed = []

    def get_entities_with(self, *args, **kwargs):
        predicate = kwargs.get("filter")
        return [entity for entity in self.entities if predicate is None or predicate(entity)]

    def remove_entity(self, entity):
        self.removed.append(entity)


class _RejectingInventory:
    def __init__(self):
        self.requested = None

    def try_add_many(self, entries):
        self.requested = list(entries)
        return False


class _ComponentState:
    def __init__(self, value):
        self.value = value


class _DroppedState:
    can_dropped = True


class Resistor:
    def __init__(self, value):
        self._label = _ComponentState(value)
        self._dropped = _DroppedState()

    def has(self, component_type):
        return component_type.__name__ in {"Dropped", "LabelComponent"}

    def get(self, component_type):
        if component_type.__name__ == "Dropped":
            return self._dropped
        if component_type.__name__ == "LabelComponent":
            return self._label
        return None


class CircuitEditorCapacityTests(unittest.TestCase):
    def test_clear_is_atomic_when_inventory_cannot_receive_all_components(self):
        component = Resistor("10")
        manager = _EditorEntityManager([component])
        inventory = _RejectingInventory()
        input_system = InputSystem.__new__(InputSystem)
        input_system.entity_manager = manager
        input_system.inventory_service = inventory
        input_system.storage_manager = _MemoryStorage()

        cleared = input_system.clear_all()

        self.assertFalse(cleared)
        self.assertEqual(manager.removed, [])
        self.assertEqual(len(inventory.requested), 1)


class MapPickupCapacityTests(unittest.TestCase):
    def setUp(self):
        self.events = EventManager.get()
        self.events.clear()

    def make_item(self):
        item = ResistorItem.__new__(ResistorItem)
        Entity.__init__(item)
        item.value = "10"
        item.area_id = 1
        item.em = self.events
        item.add(Position(10, 20))
        return item

    def test_rejected_pickup_keeps_component_on_map(self):
        item = self.make_item()
        killed = []
        self.events.subscribe("resistor_collected", lambda event: event.update(accepted=False))
        self.events.subscribe("kill_entity", killed.append)

        item.on_collect(Player.__new__(Player))

        self.assertEqual(killed, [])

    def test_accepted_pickup_removes_component_from_map(self):
        item = self.make_item()
        killed = []
        self.events.subscribe("resistor_collected", lambda event: event.update(accepted=True))
        self.events.subscribe("kill_entity", killed.append)

        item.on_collect(Player.__new__(Player))

        self.assertEqual(killed, [{"type": "kill_entity", "id": item.id}])


if __name__ == "__main__":
    unittest.main()
