import pygame
from typing import Dict
from scenes.base_scene import BaseScene
from core.managers.event_manager import EventManager
from core.settings import *
class SceneManager:
    _instance = None

    def __init__(self):
        self.scenes: Dict[str, BaseScene] = {}
        self.active_scene: BaseScene = None


        
        self.transitioning = False
        self.transition_target: BaseScene = None
        self.transition_alpha = 0
        self.transition_speed = 0
        self.transition_surface: pygame.Surface = None
        self.transition_phase = "none"  # "fade_out" ou "fade_in"

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SceneManager()
        return cls._instance

    def register(self, name: str, scene: BaseScene):
        self.scenes[name] = scene


    def change(self, name: str):
        if name not in self.scenes:
            raise KeyError(f"Scene '{name}' not registered.")
        if self.active_scene:
            self.active_scene.end()

        EventManager.get().clear()
        self.active_scene = self.scenes[name]
        self.active_scene.start()

    def start_fade(self, name: str, duration: float = 0.5):
        """Inicia a transição fade sem bloquear o loop do jogo."""
        if name not in self.scenes:
            raise KeyError(f"Scene '{name}' not registered.")
        if not self.active_scene:
            self.change(name)
            return
        EventManager.get().clear()
        self.transitioning = True
        self.transition_target = self.scenes[name]
        self.transition_phase = "fade_out"
        self.transition_alpha = 0
        self.transition_speed = 255 / (duration * FPS)  
        self.transition_surface = pygame.Surface(self.active_scene.screen.get_size())
        self.transition_surface.fill((0, 0, 0))

    def update_transition(self):
        """Chamar a cada frame antes de renderizar a cena ativa."""
        if not self.transitioning:
            return

        if self.transition_phase == "fade_out":
            self.transition_alpha += self.transition_speed
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                # troca de cena
                self.active_scene.end()
                self.active_scene = self.transition_target
                self.active_scene.start()
                self.transition_phase = "fade_in"

        elif self.transition_phase == "fade_in":
            self.transition_alpha -= self.transition_speed
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.transitioning = False
                self.transition_phase = "none"

    def draw_transition(self, surface: pygame.Surface):
        """Desenha a camada de fade sobre a cena ativa."""
        if self.transitioning:
            self.transition_surface.set_alpha(int(self.transition_alpha))
            surface.blit(self.transition_surface, (0, 0))
