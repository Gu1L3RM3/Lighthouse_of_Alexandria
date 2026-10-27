import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.navigation import NavGrid, PathFinder


class FakeLayer:
    def __init__(self, tiles):
        self._tiles = tiles

    def tiles(self):
        return [(x, y, None) for x, y in self._tiles]


class FakeTiledMap:
    # 3x3 map with an L-shaped walkable corridor: top row + right column.
    width = 3
    height = 3

    def get_layer_by_name(self, name):
        return FakeLayer([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)])


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.navgrid = NavGrid(FakeTiledMap(), 16, 16)
        self.pathfinder = PathFinder(self.navgrid)

    def test_walkable_grid_marks_layer_tiles(self):
        self.assertEqual(
            self.navgrid.walkable,
            [[True, True, True], [False, False, True], [False, False, True]],
        )

    def test_finds_path_along_walkable_tiles(self):
        path = self.pathfinder.find_path((0, 0), (2, 2))
        self.assertEqual(path, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)])

    def test_blocked_tiles_cut_the_path_without_mutating_grid(self):
        self.assertEqual(self.pathfinder.find_path((0, 0), (2, 2), {(2, 0)}), [])
        self.assertTrue(self.navgrid.walkable[0][2])

    def test_out_of_bounds_returns_empty_path(self):
        self.assertEqual(self.pathfinder.find_path((0, 0), (5, 5)), [])


if __name__ == "__main__":
    unittest.main()
