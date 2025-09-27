from core.ecs import Component
import pygame
from pygame import Surface, transform

class Sprite(Component):
    def __init__(self, image: Surface, offset_x: float = 0, offset_y: float = 0):
        self._orig_image = image.convert_alpha()
        self.image = self._orig_image.copy()
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.rect = self.image.get_rect()
        self.angle = 0.0 
         
    def rotate(self,angle_deg:float):
        self.angle = (self.angle + angle_deg) % 360
        self.image=pygame.transform.rotate(self._orig_image,self.angle)
        self.rect = self.image.get_rect(topleft=self.rect.topleft)






