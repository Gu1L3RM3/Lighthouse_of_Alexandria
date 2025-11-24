from core.ecs import Component
import pygame
from pygame import Surface
from core.managers.resource_manager import ResourceManager


class Sprite(Component):
    def __init__(self, image: Surface, offset_x: float = 0, offset_y: float = 0, angle:float=0, image_path:str|None=None):
        self._orig_image = image.convert_alpha()
        self.image_path = image_path
        self.image = self._orig_image.copy()  
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.rect = self.image.get_rect()
        self.angle = 0.0
        
        self._cached_scaled_image: Surface | None = None
        self._cache_key: tuple | None = None 

        if angle != 0:
            self.rotate(angle)
         
    def rotate(self, angle_deg:float):
        self.angle = (self.angle + angle_deg) % 360
        
        old_center = self.rect.center
        
        self.image = pygame.transform.rotate(self._orig_image, self.angle)
        self.rect = self.image.get_rect(center=old_center)
        
        self._cache_key = None 

    def get_image_for_drawing(self, scale: float) -> Surface:
        
        if scale == 1.0:
            return self.image 

        current_key = (id(self.image), scale)
        if current_key == self._cache_key:
            return self._cached_scaled_image

        w, h = self.image.get_size()
        scaled_image = pygame.transform.scale(
            self.image, (int(w * scale), int(h * scale))
        )
        
        self._cached_scaled_image = scaled_image
        self._cache_key = current_key

        return self._cached_scaled_image
    
    def to_dict(self):
        if not self.image_path:
            raise Exception("Image Path can't be Null")
        return {
            'type': self.__class__.__name__,
            'image_path': self.image_path,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'angle': self.angle,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Sprite":
        if data.get('type') != cls.__name__:
            raise ValueError("Tipo de componente inválido no dicionário de dados.")
            
        offset_x = data['offset_x']
        offset_y = data['offset_y']
        angle = data['angle']
        image_path = data['image_path']

        rm = ResourceManager.get()
        surf = rm.load_image(image_path)
        
        return cls(image=surf, offset_x=offset_x, offset_y=offset_y, angle=angle, image_path=image_path)