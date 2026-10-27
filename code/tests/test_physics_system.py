import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pygame import Rect

from core.components.collider import Collider
from core.components.position import Position
from core.components.velocity import Velocity
from core.managers.entity_manager import EntityManager
from core.systems.physics_system import PhysicsSystem


class PhysicsSystemTests(unittest.TestCase):
    def setUp(self):
        self.entity_mn = EntityManager()
        self.physics = PhysicsSystem()

    def test_moving_entity_stops_flush_against_static_wall(self):
        mover = self.entity_mn.create(Position(0, 0), Velocity(100, 0), Collider(10, 10))
        self.physics.set_external_static_colliders([Rect(500, 50, 10, 10), Rect(15, 0, 10, 10)])
        self.physics.cache_static_colliders(self.entity_mn)

        self.physics.update(self.entity_mn, 0.1)

        self.assertEqual(mover.get(Position).x, 5)
        self.assertEqual(mover.get(Velocity).vx, 0)

    def test_moving_entity_without_obstacle_moves_by_velocity(self):
        mover = self.entity_mn.create(Position(0, 0), Velocity(0, 50), Collider(10, 10))
        self.physics.set_external_static_colliders([Rect(500, 500, 10, 10)])
        self.physics.cache_static_colliders(self.entity_mn)

        self.physics.update(self.entity_mn, 0.1)

        self.assertEqual(mover.get(Position).y, 5)
        self.assertEqual(mover.get(Velocity).vy, 50)


class EntityQueryTests(unittest.TestCase):
    def setUp(self):
        self.entity_mn = EntityManager()
        self.moving = self.entity_mn.create(Position(0, 0), Velocity(1, 0))
        self.solid_moving = self.entity_mn.create(Position(0, 0), Velocity(1, 0), Collider(1, 1))
        self.static = self.entity_mn.create(Position(0, 0), Collider(1, 1))

    def test_entities_with_returns_only_entities_having_every_component(self):
        found = self.entity_mn.get_entities_with(Position, Velocity)

        self.assertCountEqual(found, [self.moving, self.solid_moving])

    def test_entities_with_applies_filter(self):
        found = self.entity_mn.get_entities_with(Position, filter=lambda e: not e.has(Velocity))

        self.assertEqual(found, [self.static])

    def test_entities_with_missing_component_returns_empty_list(self):
        self.assertEqual(self.entity_mn.get_entities_with(Position, Rect), [])


if __name__ == "__main__":
    unittest.main()
