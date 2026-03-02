from pytmx.util_pygame import load_pygame
import pytmx
import pygame
from core.map.tile_map import TileMap
from core.managers.resource_manager import ResourceManager

class TileMapLoader:
    def __init__(self):
        self.resource_mn = ResourceManager.get()

    def load(self, tmx_filename: str) -> TileMap:
        tmx_path = self.resource_mn.get_asset_path("maps", tmx_filename)
        tmx_data: pytmx.TiledMap = load_pygame(tmx_path, pixelalpha=True)

        tilemap = TileMap(tmx_data)
        
        rel_path = tmx_filename.replace('fases/', '').replace('.tmx', '')
        tilemap.tmx_file = rel_path

        ground_surface = pygame.Surface((tilemap.map_width, tilemap.map_height)).convert_alpha()
        ground_surface.fill((0, 0, 0, 0))

        for layer in self._iter_visible_layers(tmx_data, ("ground", "ground2","ground3"), pytmx.TiledTileLayer):
            for x, y, gid in layer:
                img = tmx_data.get_tile_image_by_gid(gid)
                if img:
                    ground_surface.blit(img, (x * tilemap.tile_width, y * tilemap.tile_height))

        tilemap.ground_surface = ground_surface



        for layer in self._iter_layers(tmx_data, "waypoints", pytmx.TiledObjectGroup):
            for obj in layer:
                name = (obj.name or "").lower()
                if not name:
                    continue
                tx, ty = int(obj.x // tilemap.tile_width), int(obj.y // tilemap.tile_height)
                tilemap.waypoints[name] = (tx, ty)

        return tilemap

    def _iter_layers(self, tmx_data, names: str | tuple[str, ...], layer_type):
        if isinstance(names, str):
            names = (names,)
        names = tuple(n.lower() for n in names)
        for layer in tmx_data.layers:
            if isinstance(layer, layer_type) and layer.name and layer.name.lower() in names:
                yield layer

    def _iter_visible_layers(self, tmx_data, names: str | tuple[str, ...], layer_type):
        for layer in self._iter_layers(tmx_data, names, layer_type):
            if getattr(layer, "visible", True):
                yield layer
