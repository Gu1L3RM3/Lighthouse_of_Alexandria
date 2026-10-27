import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.circuit_domain import CircuitDocument
from core.circuit_tools.circuit_repository import CircuitFormatError
from core.components.dropped import Dropped
from core.components.label_component import LabelComponent
from core.ecs import Entity
from core.systems.circuit_editor.input_system import InputSystem
from entities.circuit_editor.eletric_components import Resistor


class _EntityManager:
    def __init__(self):
        self.cleared = False
        self.entities = []

    def get_entities(self):
        return list(self.entities)

    def get_entities_by_class(self, _entity_class):
        return []

    def clear_all_entities(self):
        self.cleared = True

    def get_entities_with(self, component_type, filter=None):
        entities = [entity for entity in self.entities if entity.has(component_type)]
        return [entity for entity in entities if filter is None or filter(entity)]

    def remove_entity(self, entity):
        self.entities.remove(entity)


class _Storage:
    def __init__(self):
        self.components = {}
        self.restore_calls = 0

    def add_component(self, component_type, value):
        key = (component_type, value)
        self.components[key] = self.components.get(key, 0) + 1

    def set_completly_storage(self):
        self.restore_calls += 1

    def save_eletric_storage(self):
        pass

    def sync_baseline(self):
        pass


class _Repository:
    def __init__(self, load_error=None):
        self.saved = []
        self.load_error = load_error

    def save(self, path, document):
        self.saved.append((path, document))

    def load(self, _path):
        if self.load_error:
            raise self.load_error
        return CircuitDocument()


class _Mapper:
    def __init__(self, document):
        self.document = document

    def from_entities(self, _entities):
        return self.document

    def to_entities(self, _document):
        return []


class _Builder:
    def __init__(self):
        self.received = None

    def build(self, document):
        self.received = document
        return object()


class _Solver:
    def solve(self, _graph):
        return object()


class _Results:
    def resistor_results(self, _graph, _solution):
        return {}

    def total_values(self, _graph, _solution):
        return None


def make_system(repository):
    system = InputSystem.__new__(InputSystem)
    system.entity_manager = _EntityManager()
    system.node_manager = type("NodeManager", (), {"clear_all_nodes": lambda self: None})()
    system.storage_manager = _Storage()
    system.circuit_repository = repository
    system.circuit_mapper = _Mapper(CircuitDocument())
    system.graph_builder = _Builder()
    system.circuit_solver = _Solver()
    system.result_adapter = _Results()
    system.full_file = "test/panel"
    system.json_file = "test/panel.json"
    system.debug_mode = False
    system.resistor_results = {}
    system.total_values = None
    system.exit_current_tool = lambda: None
    system.set_empty_boxes_for_debug = lambda: None
    return system


class CircuitEditorInMemoryTests(unittest.TestCase):
    def test_save_persists_json_and_solves_without_spice_paths(self):
        repository = _Repository()
        system = make_system(repository)
        system.save_circuit()

        self.assertEqual(repository.saved, [("test/panel.json", CircuitDocument())])
        self.assertEqual(system.graph_builder.received, CircuitDocument())
        self.assertFalse(hasattr(system, "net_file"))
        self.assertFalse(hasattr(system, "lt_spice_file"))

    def test_invalid_load_preserves_current_entities(self):
        repository = _Repository(CircuitFormatError("invalid"))
        system = make_system(repository)
        with self.assertRaises(CircuitFormatError):
            system.load_circuit()
        self.assertFalse(system.entity_manager.cleared)

    def test_clear_all_returns_editable_components_to_storage(self):
        system = make_system(_Repository())
        resistor = Resistor.__new__(Resistor)
        Entity.__init__(resistor)
        resistor.components[Dropped] = Dropped()
        resistor.components[LabelComponent] = type("Label", (), {"value": "1k"})()
        system.entity_manager.entities = [resistor]

        system.clear_all()

        self.assertEqual(system.storage_manager.components, {("Resistor", "1k"): 1})
        self.assertEqual(system.storage_manager.restore_calls, 0)
        self.assertEqual(system.entity_manager.entities, [])


if __name__ == "__main__":
    unittest.main()
