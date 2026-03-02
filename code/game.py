import pygame
from core.settings               import FPS
from core.managers.event_manager import EventManager
from core.managers.scene_manager import SceneManager
from scenes.home_scene           import HomeScene
from scenes.main_menu_scene      import MainMenuScene
from scenes.fases.level_1        import Level1
from scenes.fases.level_2        import Level2
from scenes.fases.explanation_level_3 import ExplanationLevel3
from scenes.fases.explanation_level_4 import ExplanationLevel4
from scenes.fases.explanation_level_5 import ExplanationLevel5
from scenes.fases.explanation_level_6 import ExplanationLevel6
from scenes.fases.generic_level_3 import GenericLevel3
from scenes.fases.generic_level_4 import GenericLevel4
from scenes.fases.generic_level_5 import GenericLevel5
from scenes.fases.generic_level_6 import GenericLevel6
from scenes.circuit_editor       import CircuitEditor
from sys import exit
from pathlib import Path

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
        pygame.display.set_caption("Farol de Alexandria")
        self.clock = pygame.time.Clock()
        
        self.event_manager = EventManager.get()
        self.scene_manager = SceneManager.get()

    
        self.register_fases()

        self.scene_manager.change('level_1')
        
        
    def register_fases(self):
        CODE_DIR = Path(__file__).resolve().parent
        PROJECT_DIR = CODE_DIR.parent
        base_path = PROJECT_DIR / "assets" / "maps" / "fases"

        
        folder_class_map = {
            "generic_levels_3": GenericLevel3,
            "generic_levels_4": GenericLevel4,
            "generic_levels_5": GenericLevel5,
            "generic_levels_6": GenericLevel6
        }
        self.scene_manager.register('main_menu', MainMenuScene(self.screen))
        self.scene_manager.register('home_scene',HomeScene(self.screen))
        self.scene_manager.register('level_1',Level1(self.screen))
        self.scene_manager.register('level_2',Level2(self.screen))
        self.scene_manager.register('exp_fase_3', ExplanationLevel3(self.screen))
        self.scene_manager.register('exp_fase_4', ExplanationLevel4(self.screen))
        self.scene_manager.register('exp_fase_5', ExplanationLevel5(self.screen))
        self.scene_manager.register('exp_fase_6', ExplanationLevel6(self.screen))
        
        for folder, level_class in folder_class_map.items():
            folder_path = (base_path / folder)

            print(f"[DEBUG] Checking folder: {folder_path}")

            if folder_path.exists() and folder_path.is_dir():
                for file_path in folder_path.glob("*.tmx"):
                    level_name = file_path.stem
                    level_route = str(Path(folder) / level_name)  

                    self.scene_manager.register(
                        level_name,
                        level_class(self.screen, level_path=level_route)
                    )
            else:
                print(f"[WARNING] Folder not found: {folder_path}")
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            
            events = pygame.event.get()
            filtered_events = []

            for e in events:
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_q):
                    self.scene_manager.active_scene.end()
                    pygame.quit()
                    exit()
                if (
                    e.type == pygame.KEYDOWN
                    and e.key == pygame.K_ESCAPE
                    and self.scene_manager.active_scene_name != 'main_menu'
                    and not self.scene_manager.transitioning
                ):
                    self.scene_manager.open_menu(0.35)
                    continue
                filtered_events.append(e)

            self.event_manager.post(filtered_events)

            scene = self.scene_manager.active_scene
            scene.process_input(filtered_events)
            scene.update(dt)

            scene.render()

            self.scene_manager.update_transition()
            self.scene_manager.draw_transition(self.screen)

            pygame.display.flip()
