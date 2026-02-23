import pygame
from core.settings               import FPS
from core.managers.event_manager import EventManager
from core.managers.scene_manager import SceneManager
from scenes.home_scene           import HomeScene
from scenes.fases.level_1        import Level1
from scenes.fases.level_2        import Level2
from scenes.fases.level_3        import Level3
from scenes.fases.level_4        import Level4
from scenes.fases.level_5        import Level5
from scenes.circuit_editor       import CircuitEditor
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

        #self.scene_manager.active_scene = CircuitEditor(self.screen,'fase_5/pannel3',debug_mode=True)
    
        self.register_fases()
        
    def register_fases(self):
        self.scene_manager.register('level_5',Level5(self.screen))
        self.scene_manager.register('home_scene',HomeScene(self.screen))
        self.scene_manager.register('level_1',Level1(self.screen))
        self.scene_manager.register('level_2',Level2(self.screen))
        self.scene_manager.register('level_3',Level3(self.screen))
        self.scene_manager.register('level_4',Level4(self.screen))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_q):
                    self.scene_manager.active_scene.end()
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
