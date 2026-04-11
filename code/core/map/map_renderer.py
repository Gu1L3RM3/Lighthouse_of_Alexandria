import pygame
from core.map.tile_map import TileMap
from core.camera import Camera

class MapRenderer:
    def __init__(self, tilemap: TileMap, camera: Camera, screen: pygame.Surface,scale:float=1,offset:tuple[int,int]=(0,0)):
        self.tilemap = tilemap
        self.camera = camera
        self.screen = screen
        self.offset = offset
        self.map_surface = self._scale_surface(self.tilemap.ground_surface, scale)
        self.object_surface = self._scale_surface(self.tilemap.object_surface, scale)
        self.foreground_surface = self._scale_surface(self.tilemap.foreground_surface, scale)

    def _scale_surface(self, surface: pygame.Surface | None, scale: float) -> pygame.Surface | None:
        if surface is None:
            return None
        width, height = surface.get_size()
        if scale == 1:
            return surface
        return pygame.transform.scale(surface, (int(width * scale), int(height * scale)))
        
    def draw(self):
        draw_pos = (-self.camera.viewport.x + self.offset[0], -self.camera.viewport.y + self.offset[1])
        if self.map_surface is not None:
            self.screen.blit(self.map_surface, draw_pos)
        if self.tilemap.draw_static_object_layers and self.object_surface is not None:
            self.screen.blit(self.object_surface, draw_pos)

    def draw_foreground(self):
        if not self.tilemap.draw_static_object_layers:
            return
        if self.foreground_surface is None:
            return
        draw_pos = (-self.camera.viewport.x + self.offset[0], -self.camera.viewport.y + self.offset[1])
        self.screen.blit(self.foreground_surface, draw_pos)
