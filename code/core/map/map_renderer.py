import pygame
from core.map.tile_map import TileMap
from core.camera import Camera

class MapRenderer:
    def __init__(self, tilemap: TileMap, camera: Camera, screen: pygame.Surface,scale:float=1,offset:tuple[int,int]=(0,0)):
        self.tilemap = tilemap
        self.camera = camera
        self.screen = screen
        self.offset = offset
        width,height = self.tilemap.ground_surface.get_size()
        self.map_surface = pygame.transform.scale(self.tilemap.ground_surface,(int(width*scale),int(height*scale)))
        
    def draw(self):
        self.screen.blit(self.map_surface, (-self.camera.viewport.x+self.offset[0], -self.camera.viewport.y+self.offset[1]))
