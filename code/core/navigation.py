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

       
    
    def find_path(self,start_tile:tuple[int,int], goal_tile:tuple[int,int])->list[tuple[int,int]]:
        start=self.grid.node(start_tile[0],start_tile[1])

        end=self.grid.node(goal_tile[0],goal_tile[1])

        finder=AStarFinder(diagonal_movement=DiagonalMovement.never)
        path_nodes,_=finder.find_path(start,end,self.grid)
        
        return [(node.x,node.y)for node in path_nodes]
        
