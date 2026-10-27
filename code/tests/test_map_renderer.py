import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame

from core.map.map_renderer import MapRenderer

GROUND_COLOR = (10, 200, 30, 255)


class FakeTileMap:
    def __init__(self):
        self.ground_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.ground_surface.fill(GROUND_COLOR)
        self.object_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.foreground_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        self.draw_static_object_layers = True


class FakeCamera:
    viewport = pygame.Rect(0, 0, 8, 8)


class MapRendererTests(unittest.TestCase):
    def test_scaled_renderer_releases_unscaled_layers(self):
        tilemap = FakeTileMap()

        MapRenderer(tilemap, FakeCamera(), pygame.Surface((8, 8)), scale=2)

        self.assertIsNone(tilemap.ground_surface)
        self.assertIsNone(tilemap.object_surface)
        self.assertIsNone(tilemap.foreground_surface)

    def test_scaled_renderer_still_draws_ground_at_scaled_size(self):
        screen = pygame.Surface((8, 8))
        renderer = MapRenderer(FakeTileMap(), FakeCamera(), screen, scale=2)

        renderer.draw()

        self.assertEqual(tuple(screen.get_at((7, 7))), GROUND_COLOR)


if __name__ == "__main__":
    unittest.main()
