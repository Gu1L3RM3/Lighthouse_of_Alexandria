import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.managers.scene_manager import SceneManager


class FakeScene:
    def __init__(self):
        self.screen = pygame.Surface((8, 8))
        self.started = 0

    def start(self):
        self.started += 1

    def end(self):
        pass


class CountingFactory:
    def __init__(self):
        self.built: list[FakeScene] = []

    def __call__(self) -> FakeScene:
        scene = FakeScene()
        self.built.append(scene)
        return scene


class LazySceneRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.manager = SceneManager()
        self.manager.register("main_menu", FakeScene())

    def test_lazy_scene_is_not_built_until_activated(self):
        factory = CountingFactory()
        self.manager.register_lazy("fase_3", factory)

        self.assertTrue(self.manager.has_scene("fase_3"))
        self.assertEqual(factory.built, [])

    def test_lazy_scene_is_built_on_change_and_reused(self):
        factory = CountingFactory()
        self.manager.register_lazy("fase_3", factory)

        self.manager.change("fase_3")
        self.manager.change("main_menu")
        self.manager.change("fase_3")

        self.assertEqual(len(factory.built), 1)
        self.assertIs(self.manager.active_scene, factory.built[0])
        self.assertEqual(factory.built[0].started, 2)

    def test_first_lazy_registration_becomes_active_scene(self):
        manager = SceneManager()
        factory = CountingFactory()
        manager.register_lazy("main_menu", factory)

        self.assertIs(manager.active_scene, factory.built[0])
        self.assertEqual(factory.built[0].started, 1)

    def test_new_journey_rebuilds_visited_lazy_level_from_scratch(self):
        old_level = CountingFactory()
        start_level = CountingFactory()
        self.manager.register_lazy("fase_3", old_level)
        self.manager.register_lazy("level_1", start_level)
        self.manager.change("fase_3")
        self.manager.change("main_menu")

        self.manager.start_new_journey("level_1")
        self.manager.change("fase_3")

        self.assertEqual(len(old_level.built), 2)
        self.assertIs(self.manager.active_scene, old_level.built[1])

    def test_unknown_scene_is_not_registered(self):
        self.assertFalse(self.manager.has_scene("fase_99"))
        with self.assertRaises(KeyError):
            self.manager.change("fase_99")


if __name__ == "__main__":
    unittest.main()
