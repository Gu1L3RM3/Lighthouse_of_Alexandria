import pygame
from typing import Dict
from scenes.base_scene import BaseScene
from core.managers.event_manager import EventManager
from core.managers.life_manager import LifeManager
from core.managers.save_game_manager import SaveGameManager

from core.settings import *


class SceneManager:
    _instance = None

    def __init__(self):
        self.scenes: Dict[str, BaseScene] = {}
        self.active_scene: BaseScene = None
        self.active_scene_name: str | None = None

        self.scene_preview = "level_3"
        self.menu_scene_name = "main_menu"
        self.help_scene_name = "help"
        self.resume_scene_name: str | None = None
        self.help_resume_scene_name: str | None = None

        self.transitioning = False
        self.transition_target: BaseScene = None
        self.transition_target_name: str | None = None
        self.transition_alpha = 0
        self.transition_speed = 0
        self.transition_surface: pygame.Surface = None
        self.transition_phase = "none"  # "fade_out" or "fade_in"

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SceneManager()
        return cls._instance

    def register(self, name: str, scene: BaseScene):
        self.scenes[name] = scene
        if not self.active_scene:
            self.active_scene = self.scenes[name]
            self.active_scene_name = name
            self.active_scene.start()

    def change(self, name: str):
        if name not in self.scenes:
            raise KeyError(f"Scene '{name}' not registered.")
        if self.active_scene:
            self.active_scene.end()

        EventManager.get().clear()
        self.active_scene = self.scenes[name]
        self.active_scene_name = name
        self.active_scene.start()

    def can_resume_scene(self) -> bool:
        return (
            self.resume_scene_name is not None
            and self.resume_scene_name in self.scenes
            and self.resume_scene_name != self.menu_scene_name
        )

    def open_menu(self, duration: float = 0.35):
        if self.active_scene_name == self.menu_scene_name:
            return
        if self.transitioning:
            return
        self.resume_scene_name = self.active_scene_name
        self.start_fade(self.menu_scene_name, duration)

    def can_resume_help_scene(self) -> bool:
        return (
            self.help_resume_scene_name is not None
            and self.help_resume_scene_name in self.scenes
            and self.help_resume_scene_name != self.help_scene_name
        )

    def open_help(self, duration: float = 0.35):
        if self.active_scene_name == self.help_scene_name:
            return
        if self.transitioning:
            return
        self.help_resume_scene_name = self.active_scene_name
        self.start_fade(self.help_scene_name, duration)

    def resume_from_help(self, duration: float = 0.35):
        if not self.can_resume_help_scene():
            self.start_fade(self.menu_scene_name, duration)
            return
        target = self.help_resume_scene_name
        self.start_fade(target, duration)

    def resume_from_menu(self, duration: float = 0.35):
        if not self.can_resume_scene():
            return
        self.start_fade(self.resume_scene_name, duration)

    def back_with_fade(self, duration: float = 0.5):
        self.start_fade(self.scene_preview, duration)

    def start_fade(self, name: str, duration: float = 0.5):
        if name not in self.scenes:
            raise KeyError(f"Scene '{name}' not registered.")
        if not self.active_scene:
            self.change(name)
            return
        self._begin_transition(self.scenes[name], name, duration)

    def replace_scene_and_fade(self, scene_name: str, new_scene: BaseScene, duration: float = 0.5):
        if scene_name not in self.scenes:
            raise KeyError(f"Scene '{scene_name}' not registered.")
        self.scenes[scene_name] = new_scene
        if not self.active_scene:
            self.change(scene_name)
            return
        self._begin_transition(new_scene, scene_name, duration)

    def _begin_transition(self, target_scene: BaseScene, target_name: str, duration: float):
        if self.active_scene and hasattr(self.active_scene, "on_scene_will_change"):
            try:
                self.active_scene.on_scene_will_change(target_name)
            except Exception:
                pass
        EventManager.get().clear()
        self.transitioning = True
        self.transition_target = target_scene
        self.transition_target_name = target_name
        self.transition_phase = "fade_out"
        self.transition_alpha = 0
        self.transition_speed = 255 / (duration * FPS)
        self.transition_surface = pygame.Surface(self.active_scene.screen.get_size())
        self.transition_surface.fill((0, 0, 0))

    def update_transition(self):
        if not self.transitioning:
            return

        if self.transition_phase == "fade_out":
            self.transition_alpha += self.transition_speed
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.active_scene.end()
                self.active_scene = self.transition_target
                self.active_scene_name = self.transition_target_name
                self.active_scene.start()
                lives = LifeManager.get()
                SaveGameManager.get().autosave_scene(
                    self.active_scene_name,
                    current_lives=lives.current_lives,
                    max_lives=lives.max_lives,
                )
                self.transition_phase = "fade_in"

        elif self.transition_phase == "fade_in":
            self.transition_alpha -= self.transition_speed
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.transitioning = False
                self.transition_phase = "none"

    def draw_transition(self, surface: pygame.Surface):
        if self.transitioning:
            self.transition_surface.set_alpha(int(self.transition_alpha))
            surface.blit(self.transition_surface, (0, 0))
