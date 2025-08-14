import pygame
from core.config import FPS
from core.event_manager import EventManager
from core.scene_manager import SceneManager
from scenes.test_map import TestMap
from scenes.home_scene import HomeScene
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

            # Envia eventos
            self.event_manager.post(events)

            # Atualiza lógica da cena
            scene = self.scene_manager.active_scene
            scene.process_input(events)
            scene.update(dt)

            # Renderiza cena
            scene.render()

            # Atualiza e desenha transição (fade)
            self.scene_manager.update_transition()
            self.scene_manager.draw_transition(self.screen)

            pygame.display.flip()
