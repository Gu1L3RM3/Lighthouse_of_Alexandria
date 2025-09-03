import pygame
from core.components.dialogue import Dialogue
from core.components.position import Position
from core.components.collider import Collider
from core.components.freeze import Freeze
from core.managers.event_manager import EventManager
from core.managers.entity_manager import EntityManager
from core.ecs import Entity
from core.settings import *
from ui.widgets.dialogue_box import DialogueBoxWidget   # novo widget
from ui.ui_manager import UIManager


class DialogueSystem:
    
    def __init__(self, ui_manager:UIManager):
        self.event_manager = EventManager.get()
        self.active_dialogue_npc: Entity | None = None
        self.screen_size = pygame.display.get_surface().get_size()
        self.ui_manager = ui_manager   

    def update(self, entity_mn: EntityManager, player: Entity,dt):
        if self.active_dialogue_npc:
            self._handle_active_dialogue(dt)
            return
        
        self._check_for_new_dialogue(entity_mn, player)

    def _handle_active_dialogue(self,dt):
        keys = pygame.key.get_just_pressed()
        dialogue = self.active_dialogue_npc.get(Dialogue)

        dialogue.update(dt)  

        if not keys[KEY_DIALOG]:
            return
        
        if not dialogue.typewriter.finished:
            dialogue.typewriter.skip()
            return
        
        if not dialogue.next(self.screen_size):
            self._end_dialogue()

    def _check_for_new_dialogue(self, entity_mn:EntityManager, player: Entity):
        keys = pygame.key.get_just_pressed()
        if not keys[KEY_DIALOG]:
            return

        player_pos = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)

        npcs=entity_mn.get_entities_with(Dialogue,Collider)
        
        
        for npc in npcs:
            npc_pos = npc.get(Position)
            npc_col = npc.get(Collider).get_rect(npc_pos.x, npc_pos.y)

            if not player_col.colliderect(npc_col.inflate(10, 10)):
                continue
            
            self._start_dialogue(npc)
            break
    def _start_dialogue(self, npc_entity: Entity):
        self.active_dialogue_npc = npc_entity
        dialogue = npc_entity.get(Dialogue)
        dialogue.start(self.screen_size)

        freeze_comp = npc_entity.get(Freeze)
        
        if freeze_comp:
            freeze_comp.active = True

        dialog_box = DialogueBoxWidget(dialogue)
        self.ui_manager.add(dialog_box)

        self.event_manager.post({'type': 'dialogue_start', 'npc': npc_entity})

    def _end_dialogue(self):
        npc = self.active_dialogue_npc

        freeze_comp = npc.get(Freeze)
        
        if freeze_comp:
            freeze_comp.active = False

        self.ui_manager.widgets = [
            w for w in self.ui_manager.widgets if not isinstance(w, DialogueBoxWidget)
        ]

        self.active_dialogue_npc = None
        self.event_manager.post({'type': 'dialogue_end', 'npc': npc})
