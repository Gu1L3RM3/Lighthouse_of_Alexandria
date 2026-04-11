import pygame
import time
import os
from core.settings               import FPS, ASSETS_DIR
from core.managers.event_manager import EventManager
from core.managers.scene_manager import SceneManager
from core.managers.life_manager  import LifeManager
from core.managers.audio_manager import AudioManager
from core.managers.save_game_manager import SaveGameManager
from scenes.home_scene           import HomeScene
from scenes.home_after_scene     import HomeAfterScene
from scenes.main_menu_scene      import MainMenuScene
from scenes.credits_scene        import CreditsScene
from scenes.help_scene           import HelpScene
from scenes.lighthouse_rekindle_scene import LighthouseRekindleScene
from scenes.ending_thanks_credits_scene import EndingThanksCreditsScene
from scenes.fases.level_1        import Level1
from scenes.fases.level_2        import Level2
from scenes.fases.explanation_level_3 import ExplanationLevel3
from scenes.fases.explanation_level_4 import ExplanationLevel4
from scenes.fases.explanation_level_5 import ExplanationLevel5
from scenes.fases.explanation_level_6 import ExplanationLevel6
from scenes.fases.explanation_level_7 import ExplanationLevel7
from scenes.fases.generic_level_3 import GenericLevel3
from scenes.fases.generic_level_4 import GenericLevel4
from scenes.fases.generic_level_5 import GenericLevel5
from scenes.fases.generic_level_6 import GenericLevel6
from scenes.fases.generic_level_7 import GenericLevel7
from scenes.fases.final_level import FinalLevel
from scenes.circuit_editor       import CircuitEditor
from scenes.death_transition_scene import DeathTransitionScene
from pathlib import Path


class FrameProfiler:
    def __init__(self, enabled: bool = False, report_interval: float = 2.0):
        self.enabled = enabled
        self.report_interval = report_interval
        self._last_mark = 0.0
        self._elapsed = 0.0
        self._samples = 0
        self._totals = {
            "events": 0.0,
            "input": 0.0,
            "update": 0.0,
            "render": 0.0,
            "transition": 0.0,
            "flip": 0.0,
            "frame": 0.0,
        }

    def start_frame(self):
        if not self.enabled:
            return
        now = time.perf_counter()
        self._frame_start = now
        self._last_mark = now

    def mark(self, key: str):
        if not self.enabled:
            return
        now = time.perf_counter()
        self._totals[key] += (now - self._last_mark)
        self._last_mark = now

    def end_frame(self):
        if not self.enabled:
            return
        now = time.perf_counter()
        self._totals["frame"] += (now - self._frame_start)
        self._elapsed += (now - self._frame_start)
        self._samples += 1

        if self._elapsed < self.report_interval:
            return

        for key in self._totals:
            self._totals[key] = 0.0
        self._elapsed = 0.0
        self._samples = 0


class Game:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.FULLSCREEN
        )
        self._set_window_icon()
        pygame.display.set_caption("Farol de Alexandria")
        self.clock = pygame.time.Clock()
        
        self.event_manager = EventManager.get()
        self.scene_manager = SceneManager.get()
        self.life_manager = LifeManager.get()
        self.audio_manager = AudioManager.get()
        self.save_manager = SaveGameManager.get()
        self.life_manager.set_max_lives(10)
        self.life_manager.reset_lives()
        self._last_scene_name = None
        profile_enabled = os.getenv("ALEX_PROFILE", "0") == "1"
        self.profiler = FrameProfiler(enabled=profile_enabled, report_interval=2.0)

    
        self.register_fases()

        #self.scene_manager.change("exp_fase_7")
        #self.scene_manager.active_scene = CircuitEditor(self.screen,'bombs/bomb_editor',debug_mode=True)
        self._last_scene_name = self.scene_manager.active_scene_name
        self.audio_manager.on_scene_changed(self._last_scene_name)

        
    def _set_window_icon(self):
        icon_path = Path(ASSETS_DIR) / "images" / "icon" / "game_icon_64.png"


        try:
            icon = pygame.image.load(str(icon_path))
            pygame.display.set_icon(icon)
            
        except pygame.error:
            pass
            

        
    def register_fases(self):
        base_path = Path(ASSETS_DIR) / "maps" / "fases"

        
        folder_class_map = {
            "generic_levels_3": GenericLevel3,
            "generic_levels_4": GenericLevel4,
            "generic_levels_5": GenericLevel5,
            "generic_levels_6": GenericLevel6,
            "generic_levels_7": GenericLevel7,
            "final_fase": FinalLevel,
        }
        self.scene_manager.register('main_menu', MainMenuScene(self.screen))
        self.scene_manager.register('credits', CreditsScene(self.screen))
        self.scene_manager.register('help', HelpScene(self.screen))
        self.scene_manager.register('ending_lighthouse', LighthouseRekindleScene(self.screen))
        self.scene_manager.register('ending_thanks_credits', EndingThanksCreditsScene(self.screen))
        self.scene_manager.register('home_scene',HomeScene(self.screen))
        self.scene_manager.register('home_after', HomeAfterScene(self.screen))
        self.scene_manager.register('death_transition', DeathTransitionScene(self.screen))
        self.scene_manager.register('level_1',Level1(self.screen))
        self.scene_manager.register('level_2',Level2(self.screen))
        self.scene_manager.register('exp_fase_3', ExplanationLevel3(self.screen))
        self.scene_manager.register('exp_fase_4', ExplanationLevel4(self.screen))
        self.scene_manager.register('exp_fase_5', ExplanationLevel5(self.screen))
        self.scene_manager.register('exp_fase_6', ExplanationLevel6(self.screen))
        self.scene_manager.register('exp_fase_7', ExplanationLevel7(self.screen))
        
        for folder, level_class in folder_class_map.items():
            folder_path = (base_path / folder)

            if folder_path.exists() and folder_path.is_dir():
                for file_path in folder_path.glob("*.tmx"):
                    level_name = file_path.stem
                    level_route = str(Path(folder) / level_name)  

                    self.scene_manager.register(
                        level_name,
                        level_class(self.screen, level_path=level_route)
                    )
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.profiler.start_frame()
            
            events = pygame.event.get()
            self.profiler.mark("events")
            filtered_events = []

            for e in events:
                if e.type == pygame.QUIT:
                    self.save_manager.autosave_scene(
                        self.scene_manager.active_scene_name,
                        current_lives=self.life_manager.current_lives,
                        max_lives=self.life_manager.max_lives,
                    )
                    self.scene_manager.active_scene.end()
                    pygame.quit()
                    raise SystemExit
                filtered_events.append(e)

            self.event_manager.post(filtered_events)

            scene = self.scene_manager.active_scene
            if self.scene_manager.active_scene_name != self._last_scene_name:
                self._last_scene_name = self.scene_manager.active_scene_name
                self.audio_manager.on_scene_changed(self._last_scene_name)
            scene.process_input(filtered_events)
            self.profiler.mark("input")
            scene.update(dt)
            self.profiler.mark("update")

            scene.render()
            self.profiler.mark("render")

            self.scene_manager.update_transition()
            self.scene_manager.draw_transition(self.screen)
            self.profiler.mark("transition")

            pygame.display.flip()
            self.profiler.mark("flip")
            self.profiler.end_frame()
