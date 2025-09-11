import pygame
from core.map.tile_map import TileMap
from core.camera import Camera

class MapRenderer:
    def __init__(self, tilemap: TileMap, camera: Camera, screen: pygame.Surface):
        self.tilemap = tilemap
        self.camera = camera
        self.screen = screen

    def draw(self):
        if not self.tilemap.ground_surface:
            return

        map_surface = self.tilemap.ground_surface
        self.screen.blit(map_surface, (-self.camera.viewport.x, -self.camera.viewport.y))
