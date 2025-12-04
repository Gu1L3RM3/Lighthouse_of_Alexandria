import pygame
import pytmx
from core.navigation import NavGrid,PathFinder
from pathlib import Path
class TileMap:
    def __init__(self, tmx_data: pytmx.TiledMap):
        self.tmx_data    = tmx_data
        self.tmx_file    = Path(tmx_data.filename).stem
        self.tile_width  = tmx_data.tilewidth
        self.tile_height = tmx_data.tileheight
        self.map_width   = tmx_data.width * self.tile_width
        self.map_height  = tmx_data.height * self.tile_height

        self.spawn_points: dict[str, tuple[int, int]] = {}
        self.waypoints:    dict[str, tuple[int, int]] = {}

        self.ground_surface: pygame.Surface | None = None
        self.solid_colliders: list[pygame.Rect] = []
        self.navgrid = NavGrid(self.tmx_data, self.tile_width, self.tile_height, walk_layer_name="ground2")
        self.pathfinder = PathFinder(self.navgrid)


    def get_tile_from_position(self, pos) -> tuple[int, int]:
        tx = int(pos.x // self.tile_width)
        ty = int(pos.y // self.tile_height)
        return (tx, ty)
    def get_waypoint_tile(self, name: str) -> tuple[int, int] | None:
        return self.waypoints.get(name.lower())
