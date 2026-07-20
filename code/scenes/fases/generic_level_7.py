import pygame
from pygame import Vector2

from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.components.freeze import Freeze
from core.components.position import Position
from core.components.velocity import Velocity
from core.ecs import Entity
from core.localization.story_dialogue_catalog import StoryDialogueCatalog
from core.managers.language_service import LanguageService
from core.settings import KEY_DIALOG
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.max_power_transfer_validator_system import (
    MaxPowerTransferValidatorSystem,
)
from core.systems.freeze_system import FreezeSystem
from entities.dialogue_area import DialogueArea
from entities.itens.control_pannel import ControlPannel
from entities.npcs.arquimedes import Arquimedes
from entities.npcs.father import FatherNPC
from scenes.fases.max_power_level_base import BaseMaxPowerLevel


class GenericLevel7(BaseMaxPowerLevel):
    def __init__(self, screen, level_path, tolerance_percent: float = 2.0):
        self.debug_story_test_mode = False
        self.father_npc: FatherNPC | None = None
        self.father_dialogue_done = False
        self.father_escape_pending = False
        self.father_escape_delay_seconds = 3.2
        self.father_escape_timer = 0.0
        self.father_escape_speed = -70
        self.father_running = False
        self.father_disappeared = False
        self.player_can_use_door = False
        self.player_thought_dialogue: Entity | None = None
        self.player_thought_done = False
        self.player_frozen_by_story = False
        super().__init__(screen, level_path, tolerance_percent)

    def set_systems(self):
        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()
        self.circuit_validator_system = MaxPowerTransferValidatorSystem(
            level_path=self.level_path,
            tolerance_percent=self.tolerance_percent,
        )

        self.systems.update(
            [
                self.freeze_system,
                self.path_following_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.circuit_validator_system,
                self.render_system,
            ]
        )

    def start(self):
        self.father_dialogue_done = False
        self.father_escape_pending = False
        self.father_escape_timer = 0.0
        self.father_running = False
        self.father_disappeared = False
        self.player_can_use_door = False
        self.player_thought_dialogue = None
        self.player_thought_done = False
        self.player_frozen_by_story = False
        self._enforce_single_panel_mode()
        super().start()
        self._wire_story_subscribes()
        self._configure_father_dialogue()
        self._configure_arquimedes_context_hints()
        fathers = self.entity_mn.get_entities_by_class(FatherNPC)
        self.father_npc = fathers[0] if fathers else None
        self._enable_story_test_shortcut()

    def _story_catalog(self) -> StoryDialogueCatalog:
        return StoryDialogueCatalog(LanguageService.get().get_current_language())

    def _enforce_single_panel_mode(self):
        pannels = self.entity_mn.get_entities_by_class(ControlPannel)
        if not pannels:
            return

        first = pannels[0]
        first.active = True
        first.done = False
        first.panel_status.set_active(True)
        first.panel_status.set_done(False)

        for extra in pannels[1:]:
            extra.active = False
            extra.done = True
            extra.panel_status.set_active(False)
            extra.panel_status.set_done(True)

    def _configure_arquimedes_context_hints(self):
        pannels = self.entity_mn.get_entities_by_class(ControlPannel)
        active_panel = next((p for p in pannels if p.active), None)
        solution = active_panel.solution_value if active_panel else None
        target = solution.get("target", "R1") if isinstance(solution, dict) else None
        hints = self._story_catalog().get_generic_level_7_arquimedes_hints(target)

        for arquimedes in self.entity_mn.get_entities_by_class(Arquimedes):
            if not arquimedes.has(Dialogue):
                continue
            dialogue: Dialogue = arquimedes.get(Dialogue)
            dialogue.lines = hints[:]
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            area.list_dialogue = hints[:]
            dialogue.lines = hints[:]
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

    def _configure_father_dialogue(self):
        father_lines = self._story_catalog().get_generic_level_7_father_dialogue()

        for father in self.entity_mn.get_entities_by_class(FatherNPC):
            if not father.has(Dialogue):
                continue
            dialogue: Dialogue = father.get(Dialogue)
            dialogue.lines = father_lines[:]
            # Fica habilitado apenas quando o pai e libertado pelo painel.
            dialogue.active_status = False
            dialogue.auto_start = False
            dialogue.triggered = False

    def _wire_story_subscribes(self):
        # Scene transitions clear EventManager listeners. Always rebind on start.
        self.event_manager.unsubscribe("pannel_iron_gate1", self._on_father_freed)
        self.event_manager.unsubscribe("panel_solved", self._on_father_freed)
        self.event_manager.unsubscribe("dialogue_end", self._on_dialogue_end_story)
        self.event_manager.subscribe("pannel_iron_gate1", self._on_father_freed)
        self.event_manager.subscribe("panel_solved", self._on_father_freed)
        self.event_manager.subscribe("dialogue_end", self._on_dialogue_end_story)

    def _enable_story_test_shortcut(self):
        if not self.debug_story_test_mode:
            return
        # Atalho temporario para teste:
        # simula painel resolvido para abrir iron gate e habilitar dialogo do pai.
        self.event_manager.post({"type": "pannel_iron_gate1"})

    def _on_father_freed(self, event):
        if event.get("type") == "panel_solved" and event.get("pannel_id") != 1:
            return
        for father in self.entity_mn.get_entities_by_class(FatherNPC):
            if not father.has(Dialogue):
                continue
            dialogue: Dialogue = father.get(Dialogue)
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

    def _on_dialogue_end_story(self, event):
        entity = event.get("entity")
        if entity is None:
            return

        if isinstance(entity, FatherNPC) and not self.father_dialogue_done:
            self.father_dialogue_done = True
            self._start_father_escape()
            return

        if (
            self.player_thought_dialogue
            and entity.id == self.player_thought_dialogue.id
            and not self.player_thought_done
        ):
            self.player_thought_done = True
            self._finish_story_sequence()

    def _start_father_escape(self):
        if not self.father_npc:
            return
        if not self.father_npc.has(Velocity):
            return

        if self.player and self.player.has(Freeze):
            self.player.get(Freeze).active = True
            self.player_frozen_by_story = True

        # Etapa 1: abre a porta.
        if self.door:
            self.door.open({})

        # Evita travamentos de movimento por colisao/congelamento durante a fuga.
        if self.father_npc.has(Collider):
            self.father_npc.remove(Collider)
        if self.father_npc.has(Freeze):
            self.father_npc.remove(Freeze)

        # Etapa 2: pequena espera dramatica antes de ele caminhar.
        vel: Velocity = self.father_npc.get(Velocity)
        vel.vxy = (0, 0)
        self.father_npc.set_direction(Vector2(0, -1))
        self.father_escape_pending = True
        self.father_escape_timer = self.father_escape_delay_seconds
        self.father_running = False

    def _start_father_walk_to_door(self):
        if not self.father_npc or not self.father_npc.has(Velocity):
            return
        vel: Velocity = self.father_npc.get(Velocity)
        vel.vxy = (0, self.father_escape_speed)
        self.father_npc.set_direction(Vector2(0, -1))
        self.father_running = True

    def _start_player_thought_dialogue(self):
        if not self.player or not self.player.has(Position):
            return

        player_pos: Position = self.player.get(Position)
        thought = Entity()
        thought.add(
            Position(player_pos.x, player_pos.y),
            Dialogue(
                lines=self._story_catalog().get_generic_level_7_player_thought_dialogue(),
                size_dialogue=(44, 36),
                auto_start=True,
                active_status=True,
            ),
        )
        self.entity_mn.add_entity(thought)
        self.player_thought_dialogue = thought

    def _finish_story_sequence(self):
        if self.player_frozen_by_story and self.player and self.player.has(Freeze):
            self.player.get(Freeze).active = False
            self.player_frozen_by_story = False

        self.player_can_use_door = True

        if self.player_thought_dialogue:
            self.entity_mn.remove_entity(self.player_thought_dialogue)
            self.player_thought_dialogue = None

    def update(self, dt):
        super().update(dt)
        self._update_story_sequence(dt)

    def _update_story_sequence(self, dt: float):
        if self.father_escape_pending:
            self.father_escape_timer -= dt
            if self.father_escape_timer <= 0:
                self.father_escape_pending = False
                self._start_father_walk_to_door()

        if not self.father_running or not self.father_npc or not self.father_npc.has(Position):
            return

        father_pos: Position = self.father_npc.get(Position)
        target_y = 96
        if self.door and self.door.has(Position):
            door_pos: Position = self.door.get(Position)
            target_y = door_pos.y + 8

        if father_pos.y > target_y:
            return

        if self.father_npc.has(Velocity):
            self.father_npc.get(Velocity).vxy = (0, 0)
        self.father_npc.set_direction(Vector2(0, 0))
        self.father_running = False
        self.father_disappeared = True
        self.entity_mn.remove_entity(self.father_npc)
        self.father_npc = None
        self._start_player_thought_dialogue()

    def _handle_panel_interaction(self, events):
        player = self.entity_mn.get_player()
        if not player:
            self.interaction_key_widget.set_visible(False)
            return

        target_panel = None
        for panel in self.entity_mn.get_entities_by_class(ControlPannel):
            if panel.can_player_interact(player):
                target_panel = panel
                break

        can_use_door = (
            self.player_can_use_door
            and self.door
            and self.door.can_player_interact(player)
        )
        target_door = self.door if can_use_door else None

        self.dialogue_hud.update(
            player,
            extra_interaction=(target_panel is not None or target_door is not None),
        )
        if not target_panel and not target_door:
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                if target_panel:
                    target_panel.open_circuit_editor()
                elif target_door:
                    target_door.try_enter(player)
                self.interaction_key_widget.set_visible(False)
                break

    def update_storage_circuit_generic(self, event, component_type):
        return super().update_storage_circuit_generic(event, component_type)
