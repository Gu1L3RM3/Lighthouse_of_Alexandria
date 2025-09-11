import pygame
from core.settings import FPS
from core.managers.event_manager import EventManager
from core.managers.scene_manager import SceneManager
from scenes.test_map import TestMap
from scenes.home_scene import HomeScene
from scenes.puzzle_map import PuzzleMap
from sys import exit

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
        self.scene_manager.register('teste', TestMap(self.screen))
        self.scene_manager.register('home', HomeScene(self.screen))
        self.scene_manager.register('puzzle',PuzzleMap(self.screen))

        
        self.scene_manager.active_scene = HomeScene(self.screen)
        self.scene_manager.active_scene.start()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    exit()

            self.event_manager.post(events)

            scene = self.scene_manager.active_scene
            scene.process_input(events)
            scene.update(dt)

            scene.render()

            self.scene_manager.update_transition()
            self.scene_manager.draw_transition(self.screen)

            pygame.display.flip()
