import pygame
import os 
from core.settings import *
class ResourceManager:
    _instance = None

    def __init__(self):
        self._images = {}
        self._sounds = {}
        self._fonts = {}

    

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ResourceManager()
        return cls._instance
    
 
    def get_asset_path(self,subdir: str, filename: str) -> str:
        return os.path.join(ASSETS_DIR, subdir, filename)

    def load_image(self, filename: str, colorkey=None, size: tuple[int, int] | None = None) -> pygame.Surface:
        
        key = (filename, size)  
        if key not in self._images:
            path = self.get_asset_path('images', filename)
            img = pygame.image.load(path).convert_alpha()

            if colorkey is not None:
                img.set_colorkey(colorkey)

            
            if size is not None:
                img = pygame.transform.scale(img, size)

            self._images[key] = img

        return self._images[key]


    def load_sound(self, filename: str) -> pygame.mixer.Sound:
        if filename not in self._sounds:
            path = self.get_asset_path('sounds', filename)
            snd = pygame.mixer.Sound(path)
            self._sounds[filename] = snd
        return self._sounds[filename]

    def load_font(self, filename: str, size: int) -> pygame.font.Font:
        key = f"{filename}-{size}"
        if key not in self._fonts:
            path = self.get_asset_path('fonts', filename)
            font = pygame.font.Font(path, size)
            self._fonts[key] = font
        return self._fonts[key]
    
    def _cut_sprite_sheet(self, 
                        image_path: str,
                        size_sprite: tuple = (48, 48),
                        offset: tuple[int, int] = (0, 0),
                        scale: float = 1.0,
                        trim_transparent: bool = True) -> list[pygame.Surface]:
        sprites = []
        width_sprite, height_sprite = size_sprite

        image = pygame.image.load(image_path).convert_alpha()
        width, height = image.get_size()

        columns = width // width_sprite
        lines = height // height_sprite

        for line in range(lines):
            for column in range(columns):
                posx = column * width_sprite + offset[0]
                posy = line * height_sprite + offset[1]

                rect = pygame.Rect(posx, posy, width_sprite, height_sprite)
                sub_surf = image.subsurface(rect).copy()

                bounding_box = sub_surf.get_bounding_rect()
                if bounding_box.width == 0 and bounding_box.height == 0:
                    continue

                if trim_transparent:
                    sub_surf = sub_surf.subsurface(bounding_box).copy()

                if scale != 1.0:
                    new_width = max(1, int(sub_surf.get_width() * scale))
                    new_height = max(1, int(sub_surf.get_height() * scale))
                    sub_surf = pygame.transform.smoothscale(sub_surf, (new_width, new_height))

                sprites.append(sub_surf)

        return sprites

        

                

    def load_sprite_sheet(self,subdir: str ,size:tuple[int]=(48,48),offset:tuple[int]=(0,0),scale:float=1.0,trim_transparent:bool=True ):
        dict_assets:dict={}
        main_file =self.get_asset_path('images',subdir)
        for dirpath, _ , filenames in os.walk(main_file):
            if not filenames :
                continue

            name_subdir=os.path.basename(dirpath)

            if  name_subdir == '':
                continue

            image_path = os.path.join(dirpath,filenames[0])
            sprites= self._cut_sprite_sheet(image_path,size,offset,scale,trim_transparent)
            dict_assets[name_subdir]=sprites
        return dict_assets