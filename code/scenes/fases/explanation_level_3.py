from pygame import Surface

from core.components.dialogue import Dialogue
from core.settings import EXPLANATION_LEVEL3_BOMB_INTRO_LINES
from entities.dialogue_area import DialogueArea
from scenes.fases.explanation_content import get_phase_dialogue_media
from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel3(BaseExplanationLevel):
    BOMB_INTRO_LINES = list(EXPLANATION_LEVEL3_BOMB_INTRO_LINES)

    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_3",
            next_scene="fase_3",
        )
        self._dialog_1_base_lines = self._get_dialog_1_base_lines()

    def start(self):
        self._configure_bomb_intro_dialogue()
        super().start()

    def _configure_bomb_intro_dialogue(self):
        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if area.name != "dialog_1" or not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            merged_lines = self._dialog_1_base_lines + self.BOMB_INTRO_LINES
            area.list_dialogue = merged_lines[:]
            dialogue.lines = merged_lines[:]
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False
            break

    def _get_dialog_1_base_lines(self) -> list[str]:
        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if area.name != "dialog_1" or not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            return list(dialogue.lines or area.list_dialogue or [])
        return []

    def get_dialogue_image_sequences(self) -> dict:
        return get_phase_dialogue_media("exp_fase_3")
