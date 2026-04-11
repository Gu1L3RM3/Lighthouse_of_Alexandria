import pygame
from core.components.dialogue import Dialogue
from core.components.position import Position
from core.components.collider import Collider
from core.managers.event_manager import EventManager
from core.managers.entity_manager import EntityManager
from core.ecs import Entity
from core.settings import *
from core.managers.input_manager import InputManager
from core.ui.widgets.dialog_box import DialogueBoxWidget  
from core.managers.ui_manager import UIManager
from entities.dialogue_area import DialogueArea



class DialogueSystem:
    def __init__(self, ui_manager:UIManager):
        self.event_manager = EventManager.get()
        self.input_manager = InputManager.get()
        self.active_dialogue: Entity | None = None
        self.screen_size = pygame.display.get_surface().get_size()
        self.ui_manager = ui_manager 

    def update(self, entity_mn: EntityManager, player: Entity,dt):
        if self.active_dialogue:
            self._handle_active_dialogue(dt)
            return
        
        self._check_for_new_dialogue(entity_mn, player)

    def _handle_active_dialogue(self,dt):
        dialogue = self.active_dialogue.get(Dialogue)

        dialogue.update(dt)  

        if not self.input_manager.is_key_just_pressed(KEY_DIALOG):
            return
        
        if not dialogue.typewriter.finished:
            dialogue.typewriter.skip()
            return
        
        if not dialogue.next(self.screen_size):
            self._end_dialogue()


        
        
    def _check_for_new_dialogue(self, entity_mn:EntityManager, player: Entity):
        player_pos = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)

        entities = entity_mn.get_entities_with(Dialogue)
        # Prioriza áreas de diálogo sobre diálogos de NPC e mantém ordem estável.
        entities = sorted(
            entities,
            key=lambda e: (0 if isinstance(e, DialogueArea) else 1, e.id)
        )
        
        
        for entity in entities:
            entity_pos :Position= entity.get(Position)
            entity_dialogue :Dialogue= entity.get(Dialogue)
            entity_area_dialogue = entity_dialogue.get_area(entity_pos.x,entity_pos.y)
     
            if not player_col.colliderect(entity_area_dialogue.inflate(10, 10)):
                continue
            if not entity_dialogue.active_status:
                continue

            if entity_dialogue.auto_start and not entity_dialogue.triggered:
                entity_dialogue.triggered = True
                self._start_dialogue(entity,player)
                break

            elif not entity_dialogue.auto_start and self.input_manager.is_key_just_pressed(KEY_DIALOG):
                self._start_dialogue(entity,player)
                break
    

    def _start_dialogue(self, entity: Entity,player:Entity):
        player.stay_idle()

        self.active_dialogue= entity

        dialogue = entity.get(Dialogue)
        dialogue.start(self.screen_size)

        self.event_manager.post({'type':'request_freeze','type_request':'dialogue'})

        dialog_box = DialogueBoxWidget(dialogue)
        self.ui_manager.add(dialog_box)

        self.event_manager.post({'type': 'dialogue_start', 'entity': entity})
    def _end_dialogue(self):
        entity = self.active_dialogue

        self.event_manager.post({'type':'release_freeze'})

        self.ui_manager.widgets = [
            w for w in self.ui_manager.widgets if not isinstance(w, DialogueBoxWidget)
        ]

        if isinstance(entity, DialogueArea) and entity.can_grant_stealth_bonus():
            self.event_manager.post({
                "type": "player_invisible_to_enemies_started",
                "duration": entity.stealth_bonus_duration,
                "source": "area_dialog",
                "dialog_name": entity.name,
            })
            entity.mark_stealth_bonus_consumed()

        self.active_dialogue = None
        self.event_manager.post({'type': 'dialogue_end', 'entity': entity})
