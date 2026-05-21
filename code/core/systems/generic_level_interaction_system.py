import pygame

from core.ecs import System
from core.components.area_trigger import AreaTrigger
from core.components.collider import Collider
from core.components.position import Position
from core.managers.language_service import LanguageService
from core.settings import KEY_DIALOG
from core.ui.widgets.alert_dialog import AlertDialog
from entities.itens.control_pannel import ControlPannel
from entities.itens.old_paper import OldPaper


class GenericLevelInteractionSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def update(self, entity_mn, dt: float):
        _ = entity_mn
        _ = dt

    def get_modal_alert_dialog(self):
        for widget in self.scene.ui_manager.widgets:
            if isinstance(widget, AlertDialog):
                return widget
        return None

    def handle_panel_interaction(self, events: list[pygame.event.Event]):
        player = self.scene.entity_mn.get_player()
        if not player:
            self.scene.interaction_key_widget.set_visible(False)
            return

        target_panel = None
        for panel in self.scene.entity_mn.get_entities_by_class(ControlPannel):
            if panel.can_player_interact(player):
                target_panel = panel
                break

        target_door = self._resolve_target_door(player)
        self.scene.dialogue_hud.update(
            player,
            extra_interaction=(target_panel is not None or target_door is not None),
        )
        if not target_panel and not target_door:
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                if target_panel:
                    self.scene.audio_manager.play_sfx("sfx/interact_confirm.wav", volume=0.9)
                    target_panel.open_circuit_editor()
                elif target_door:
                    target_door.try_enter(player)
                self.scene.interaction_key_widget.set_visible(False)
                break

    def _resolve_target_door(self, player):
        door = getattr(self.scene, "door", None)
        if door and door.can_player_interact(player):
            return door
        return None

    def can_old_paper_interact(self) -> bool:
        old_papers = self.scene.entity_mn.get_entities_by_class(OldPaper)
        if not old_papers:
            return False
        paper = old_papers[0]
        if not paper.has(AreaTrigger) or not paper.has(Position):
            return False
        if not self.scene.player or not self.scene.player.has(Position) or not self.scene.player.has(Collider):
            return False

        trigger: AreaTrigger = paper.get(AreaTrigger)
        pos: Position = paper.get(Position)
        if not trigger or not pos:
            return False

        rect = trigger.get_rect(pos.x, pos.y)
        player_rect = self.scene.player.get(Collider).get_rect(*self.scene.player.get(Position).pos)
        return rect.colliderect(player_rect)

    def handle_old_paper_interaction(self, events: list[pygame.event.Event]):
        can_interact = self.can_old_paper_interact()
        if can_interact:
            self.scene.dialogue_hud.update(self.scene.player, extra_interaction=True)
        for event in events:
            if (
                can_interact
                and event.type == pygame.KEYDOWN
                and event.key == KEY_DIALOG
            ):
                self.scene.event_manager.post({"type": "open_old_paper"})
                break

    def resolve_interaction_prompt(self, player) -> str | None:
        if not player:
            return None
        language = LanguageService.get()

        for panel in self.scene.entity_mn.get_entities_by_class(ControlPannel):
            if panel.can_player_interact(player):
                return language.get_ui_label("open")

        if self._resolve_target_door(player):
            return language.get_ui_label("enter")

        if self.can_old_paper_interact():
            return language.get_ui_label("read")

        return None
