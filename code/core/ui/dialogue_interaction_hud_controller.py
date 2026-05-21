from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.components.position import Position
from core.managers.entity_manager import EntityManager
from core.managers.language_service import LanguageService
from core.systems.dialogue_system import DialogueSystem
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from entities.dialogue_area import DialogueArea


class DialogueInteractionHUDController:
    def __init__(
        self,
        entity_mn: EntityManager,
        dialogue_system: DialogueSystem,
        widget: InteractionKeyWidget,
    ):
        self.entity_mn = entity_mn
        self.dialogue_system = dialogue_system
        self.widget = widget

    def update(self, player, extra_interaction: bool = False, extra_prompt_label: str | None = None):
        if self.dialogue_system.active_dialogue:
            self.widget.set_visible(False)
            return

        language = LanguageService.get()
        if extra_prompt_label is None:
            extra_prompt_label = language.get_ui_label("interact")
        has_dialogue_interaction = self._find_dialogue_interaction_target(player) is not None
        if has_dialogue_interaction:
            self.widget.set_prompt("interact", language.get_ui_label("talk"))
        else:
            self.widget.set_prompt("interact", extra_prompt_label)
        self.widget.set_visible(bool(extra_interaction or has_dialogue_interaction))

    def _find_dialogue_interaction_target(self, player):
        if not player or not player.has(Position) or not player.has(Collider):
            return None

        player_pos = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)

        for entity in self.entity_mn.get_entities_with(Dialogue, Position):
            dialogue: Dialogue = entity.get(Dialogue)
            if dialogue.auto_start or not dialogue.active_status:
                continue
            entity_pos: Position = entity.get(Position)
            area = dialogue.get_area(entity_pos.x, entity_pos.y)
            if isinstance(entity, DialogueArea):
                area = area.inflate(10, 10)
            else:
                # Keep HUD interaction radius aligned with DialogueSystem collision check.
                area = area.inflate(10, 10)
            if player_col.colliderect(area):
                return entity
        return None
