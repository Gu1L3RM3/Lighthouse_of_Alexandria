import numpy as np
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement
from pytmx import TiledMap
from core.settings import *

class NavGrid:
    def __init__(self,tmx_data:TiledMap,
                 tile_width:int,
                 tile_height:int,
                 walk_layer_name="ground2"):
        
        self.tmx_data=tmx_data
        self.layer_name=walk_layer_name
        self.tile_width=tile_width
        self.tile_height=tile_height

        self.map_width=self.tmx_data.width
        self.map_height=self.tmx_data.height

        self.walkable=np.zeros((self.map_height,self.map_width),dtype=bool)
        self._set_walkable()
    def _set_walkable(self):
        layer=self.tmx_data.get_layer_by_name(self.layer_name)
        for x,y,_ in layer.tiles():
          self.walkable[y][x]=True
    
class PathFinder:
    def __init__(self,navgrid:NavGrid):
        self.walkable=navgrid.walkable
        self.grid=Grid(matrix=self.walkable)
        
    def _in_bounds(self, tile: tuple[int, int]) -> bool:
        x, y = tile
        return 0 <= x < self.walkable.shape[1] and 0 <= y < self.walkable.shape[0]

    def find_path(
        self,
        start_tile:tuple[int,int],
        goal_tile:tuple[int,int],
        blocked_tiles: set[tuple[int, int]] | None = None
    )->list[tuple[int,int]]:
        if not self._in_bounds(start_tile) or not self._in_bounds(goal_tile):
            return []

        grid = self.grid
        if blocked_tiles:
            matrix = self.walkable.copy()
            for bx, by in blocked_tiles:
                if (bx, by) == start_tile or (bx, by) == goal_tile:
                    continue
                if self._in_bounds((bx, by)):
                    matrix[by][bx] = False
            grid = Grid(matrix=matrix)

        grid.cleanup()
        start=grid.node(start_tile[0],start_tile[1])
        end=grid.node(goal_tile[0],goal_tile[1])

        finder=AStarFinder(diagonal_movement=DiagonalMovement.never)
        path_nodes,_=finder.find_path(start,end,grid)
        
        return [(node.x,node.y)for node in path_nodes]
        
