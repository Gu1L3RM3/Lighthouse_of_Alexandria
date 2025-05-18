import pygame
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from core.event_manager import EventManager
from core.scene_manager import SceneManager
from scenes.teste_scene import TestScene
from scenes.home_scene import HomeScene
from sys import exit
class Game:
    def __init__(self):
        pygame.init()
        self.screen= pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),pygame.FULLSCREEN)
        pygame.display.set_caption("Farol de Alexandria")
        self.clock = pygame.time.Clock()
        
        self.event_manager = EventManager.get()
        self.scene_manager = SceneManager.get()
        self.scene_manager.active_scene =TestScene(self.screen)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()


            self.event_manager.post(events)

            scene = self.scene_manager.active_scene
            scene.process_input(events)
            scene.update(dt)
            scene.render()

            pygame.display.flip()

        
