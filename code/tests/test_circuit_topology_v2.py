import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitElement, ElementKind
from core.circuit_tools.circuit_topology import CircuitGraphBuilder, CircuitTopologyIndex


class CircuitTopologyTests(unittest.TestCase):
    def setUp(self):
        self.builder = CircuitGraphBuilder(cell_size=64)

    def test_voltage_source_vertical_polarity(self):
        source_90 = CircuitElement(ElementKind.VOLTAGE_SOURCE, 128, 256, 90, name="V1", value="12")
        source_270 = CircuitElement(ElementKind.VOLTAGE_SOURCE, 128, 256, 270, name="V1", value="12")
        top = (160, 256)
        bottom = (160, 384)
        self.assertEqual(self.builder.terminals_for(source_90), {"pos": top, "neg": bottom})
        self.assertEqual(self.builder.terminals_for(source_270), {"neg": top, "pos": bottom})

    def test_current_source_vertical_polarity(self):
        source_90 = CircuitElement(ElementKind.CURRENT_SOURCE, 128, 256, 90, name="I1", value="1")
        source_270 = CircuitElement(ElementKind.CURRENT_SOURCE, 128, 256, 270, name="I1", value="1")
        top = (160, 256)
        bottom = (160, 384)
        self.assertEqual(self.builder.terminals_for(source_90), {"to": top, "from": bottom})
        self.assertEqual(self.builder.terminals_for(source_270), {"from": top, "to": bottom})

    def test_builds_grounded_parallel_branches(self):
        document = CircuitDocument(
            elements=(
                CircuitElement(ElementKind.VOLTAGE_SOURCE, 0, 0, 90, name="V1", value="10"),
                CircuitElement(ElementKind.RESISTOR, 0, 0, 90, name="R1", value="1k"),
                CircuitElement(ElementKind.GROUND, 0, 128),
                CircuitElement(ElementKind.NODE, 0, -64),
                CircuitElement(ElementKind.NODE, 0, 128),
            )
        )
        graph = self.builder.build(document)
        self.assertTrue(graph.has_ground)
        self.assertEqual(len(graph.branches), 2)
        self.assertEqual(graph.branches[0].positive_node, graph.branches[1].positive_node)
        self.assertEqual(graph.branches[0].negative_node, 0)
        self.assertEqual(graph.branches[1].negative_node, 0)

    def test_incremental_index_tracks_only_affected_positions_and_revisions(self):
        resistor = CircuitElement(ElementKind.RESISTOR, 0, 0, name="R1", value="1k")
        index = CircuitTopologyIndex(64, CircuitDocument((resistor,)))

        resistor_id = index.element_ids[0]
        index.replace(
            resistor_id,
            CircuitElement(ElementKind.RESISTOR, 0, 0, name="R1", value="2k"),
        )
        self.assertEqual(index.topology_revision, 0)
        self.assertEqual(index.value_revision, 1)
        self.assertEqual(index.last_affected_positions, frozenset())

        index.replace(
            resistor_id,
            CircuitElement(ElementKind.RESISTOR, 64, 0, name="R1", value="2k"),
        )
        self.assertEqual(index.topology_revision, 1)
        self.assertEqual(
            index.last_affected_positions,
            frozenset({(0, 32), (128, 32), (64, 32), (192, 32)}),
        )


if __name__ == "__main__":
    unittest.main()
