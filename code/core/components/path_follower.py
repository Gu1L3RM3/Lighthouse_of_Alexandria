import pygame
from pygame import Vector2
from core.ecs import Component
from core.settings import *
class PathFollower(Component):
    def __init__(self,path: list[tuple[int, int]],speed: float = 40):
    
        
        self.path:list[tuple[int,int]]=[]
        self.current_index = 0
        self.speed = speed  
        self.done = len(self.path) == 0
        self.direction = Vector2(0, 0)
        self.set_path(path)

    def create_collision_rects(self):
        if not self.path:
            return
        self.collision_rects:list[pygame.Rect]=[]
        for point in self.path:
            x= (point[0]*TILE_SIZE)+TILE_SIZE//2
            y= (point[1]*TILE_SIZE)+TILE_SIZE//2

            rect= pygame.Rect((x,y),(2,2))
            self.collision_rects.append(rect)
        
        
    def set_path(self, new_path: list[tuple[int, int]]):
        
        
        path_copy = list(new_path) 
        
        
        if len(path_copy) > 1:
            path_copy.pop(0)

        self.path = path_copy
        self.done = not bool(self.path)
        self.direction = Vector2(0, 0) 
        self.create_collision_rects()
    def to_dict(self):
        return {
            'type':self.__class__.__name__,
            'path':self.path,
            'speed':self.speed
        }
