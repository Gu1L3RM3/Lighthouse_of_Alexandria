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
from entities.npcs.arquimedes import Arquimedes
from entities.npcs.father import FatherNPC



class DialogueSystem:
    NPC_DIALOG_FOCUS_MAX_DISTANCE = 128.0

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
                self._start_dialogue(entity_mn, entity, player)
                break

            elif not entity_dialogue.auto_start and self.input_manager.is_key_just_pressed(KEY_DIALOG):
                self._start_dialogue(entity_mn, entity, player)
                break
    

    def _get_entity_center(self, entity: Entity) -> pygame.Vector2 | None:
        if not entity.has(Position):
            return None
        pos: Position = entity.get(Position)
        return pos.center_pos()

    def _get_dialogue_area_rect(self, area: DialogueArea) -> pygame.Rect | None:
        if not area.has(Position) or not area.has(Dialogue):
            return None
        pos: Position = area.get(Position)
        dialogue: Dialogue = area.get(Dialogue)
        return dialogue.get_area(pos.x, pos.y)

    def _distance_sq_point_to_rect(self, point: pygame.Vector2, rect: pygame.Rect) -> float:
        dx = 0.0
        if point.x < rect.left:
            dx = float(rect.left - point.x)
        elif point.x > rect.right:
            dx = float(point.x - rect.right)

        dy = 0.0
        if point.y < rect.top:
            dy = float(rect.top - point.y)
        elif point.y > rect.bottom:
            dy = float(point.y - rect.bottom)

        return dx * dx + dy * dy

    def _nearest_dialogue_npc_for_area(self, entity_mn: EntityManager, area_rect: pygame.Rect) -> pygame.Vector2 | None:
        if area_rect is None:
            return None

        nearest = None
        nearest_dist_sq = None
        candidates = []
        candidates.extend(entity_mn.get_entities_by_class(Arquimedes))
        candidates.extend(entity_mn.get_entities_by_class(FatherNPC))

        for npc in candidates:
            center = self._get_entity_center(npc)
            if center is None:
                continue
            dist_sq = self._distance_sq_point_to_rect(center, area_rect)
            if nearest is None or dist_sq < nearest_dist_sq:
                nearest = center
                nearest_dist_sq = dist_sq

        if nearest is None:
            return None

        max_dist_sq = self.NPC_DIALOG_FOCUS_MAX_DISTANCE * self.NPC_DIALOG_FOCUS_MAX_DISTANCE
        if nearest_dist_sq > max_dist_sq:
            return None

        return nearest

    def _resolve_dialogue_focus_target(self, entity_mn: EntityManager, dialogue_entity: Entity) -> pygame.Vector2 | None:
        if isinstance(dialogue_entity, (Arquimedes, FatherNPC)):
            return self._get_entity_center(dialogue_entity)

        if isinstance(dialogue_entity, DialogueArea):
            area_rect = self._get_dialogue_area_rect(dialogue_entity)
            return self._nearest_dialogue_npc_for_area(entity_mn, area_rect)

        return None

    def _start_dialogue(self, entity_mn: EntityManager, entity: Entity, player: Entity):
        player.stay_idle()
        focus_target = self._resolve_dialogue_focus_target(entity_mn, entity)
        if focus_target is not None and hasattr(player, "look_at_world_position"):
            player.look_at_world_position(focus_target)

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
