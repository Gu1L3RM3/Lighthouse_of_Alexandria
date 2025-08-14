import pygame
from core.components.dialogue import Dialogue
from core.components.position import Position
from core.components.collider import Collider
from core.event_manager import EventManager

class DialogueSystem:
    def __init__(self):
        self.event_manager = EventManager.get()
        self.active_dialogue = None
        self.screen_size = pygame.display.get_surface().get_size()

    def update(self, entities, player):
        keys=pygame.key.get_just_pressed()
        if self.active_dialogue:
            dialogue = self.active_dialogue.get(Dialogue)
            dialogue.update()

            # pular typewriter (mostrar tudo)
            if keys[pygame.K_e]:
                if not dialogue.typewriter.finished:
                    dialogue.typewriter.skip()
                else:
                    if not dialogue.next(self.screen_size):
                        self.active_dialogue = None
                        self.event_manager.post(
                            {'type': 'dialogue_end', 'npc': self.active_dialogue}
                        )
            return

        # checa proximidade do player
        player_pos = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)

        for e in entities:
            if e.has(Dialogue) and e.has(Position) and e.has(Collider):
                npc_pos = e.get(Position)
                npc_col = e.get(Collider).get_rect(npc_pos.x, npc_pos.y)

                if player_col.colliderect(npc_col.inflate(10, 10)):
                    if keys[pygame.K_e]:
                        self.active_dialogue = e
                        
                        e.get(Dialogue).start(self.screen_size)
                        self.event_manager.post(
                            {'type': 'dialogue_start', 'npc': e}
                        )
                        break

    def draw(self, screen):
        if not self.active_dialogue:
            return
        dialogue = self.active_dialogue.get(Dialogue)
        dialogue.draw(screen)
