import pygame
from core.config import get_asset_path

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

    def load_image(self, filename: str, colorkey=None) -> pygame.Surface:
        if filename not in self._images:
            path = get_asset_path('images', filename)
            img = pygame.image.load(path).convert_alpha()

            if colorkey is not None:
                img.set_colorkey(colorkey)
            self._images[filename] = img

        return self._images[filename]

    def load_sound(self, filename: str) -> pygame.mixer.Sound:
        if filename not in self._sounds:
            path = get_asset_path('sounds', filename)
            snd = pygame.mixer.Sound(path)
            self._sounds[filename] = snd
        return self._sounds[filename]

    def load_font(self, filename: str, size: int) -> pygame.font.Font:
        key = f"{filename}-{size}"
        if key not in self._fonts:
            path = get_asset_path('fonts', filename)
            font = pygame.font.Font(path, size)
            self._fonts[key] = font
        return self._fonts[key]
