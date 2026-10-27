import pygame
from typing import Callable, Dict
from scenes.base_scene import BaseScene
from core.managers.event_manager import EventManager
from core.managers.life_manager import LifeManager
from core.managers.save_game_manager import SaveGameManager
from core.managers.scene_factory import SceneFactory

from core.settings import *


class SceneManager:
    _instance = None

    def __init__(self):
        self.scenes: Dict[str, BaseScene] = {}
        self._scene_factories: Dict[str, Callable[[], BaseScene]] = {}
        self._scenes_needing_reset: set[str] = set()
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

    def register_lazy(self, name: str, factory: Callable[[], BaseScene]):
        # Levels load and scale their whole map on construction; building them only
        # when first visited keeps unvisited levels out of RAM.
        self._scene_factories[name] = factory
        if not self.active_scene:
            self.register(name, factory())

    def has_scene(self, name: str) -> bool:
        return name in self.scenes or name in self._scene_factories

    def get_scene(self, name: str) -> BaseScene:
        if name not in self.scenes:
            if name not in self._scene_factories:
                raise KeyError(f"Scene '{name}' not registered.")
            self.scenes[name] = self._scene_factories[name]()
        return self.scenes[name]

    def _recreate_scene_instance(self, name: str) -> BaseScene:
        factory = self._scene_factories.get(name)
        if factory is not None:
            recreated = factory()
        else:
            recreated = SceneFactory.get().recreate(self.get_scene(name))
        self.scenes[name] = recreated
        self._scenes_needing_reset.discard(name)
        return recreated

    def _resolve_scene_for_activation(self, name: str) -> BaseScene:
        if name in self._scenes_needing_reset:
            return self._recreate_scene_instance(name)
        return self.get_scene(name)

    def start_new_journey(self, start_scene_name: str = "home_scene", duration: float = 0.6):
        save_manager = SaveGameManager.get()
        self.resume_scene_name = None
        self.help_resume_scene_name = None

        # Marca apenas cenas de gameplay para reset; menu/help/creditos permanecem.
        for scene_name in list(self.scenes.keys()):
            if not save_manager.should_persist_scene(scene_name):
                continue
            if scene_name in self._scene_factories and self.scenes[scene_name] is not self.active_scene:
                # Dropping a built lazy scene frees its map; its factory rebuilds it fresh on the next visit.
                del self.scenes[scene_name]
            else:
                self._scenes_needing_reset.add(scene_name)

        # A cena inicial da nova jornada precisa estar limpa imediatamente.
        if self.has_scene(start_scene_name):
            self._recreate_scene_instance(start_scene_name)

        self.start_fade(start_scene_name, duration)

    def change(self, name: str):
        if not self.has_scene(name):
            raise KeyError(f"Scene '{name}' not registered.")
        if self.active_scene:
            self.active_scene.end()

        EventManager.get().clear()
        self.active_scene = self._resolve_scene_for_activation(name)
        self.active_scene_name = name
        self.active_scene.start()

    def can_resume_scene(self) -> bool:
        return (
            self.resume_scene_name is not None
            and self.has_scene(self.resume_scene_name)
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
            and self.has_scene(self.help_resume_scene_name)
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
        if not self.has_scene(name):
            raise KeyError(f"Scene '{name}' not registered.")
        if not self.active_scene:
            self.change(name)
            return
        target_scene = self._resolve_scene_for_activation(name)
        self._begin_transition(target_scene, name, duration)

    def replace_scene_and_fade(self, scene_name: str, new_scene: BaseScene, duration: float = 0.5):
        if not self.has_scene(scene_name):
            raise KeyError(f"Scene '{scene_name}' not registered.")
        self.scenes[scene_name] = new_scene
        self._scenes_needing_reset.discard(scene_name)
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
