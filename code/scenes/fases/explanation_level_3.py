from pygame import Surface

from core.components.dialogue import Dialogue
from core.localization.scene_copy_catalog import SceneCopyCatalog
from core.managers.language_service import LanguageService
from entities.dialogue_area import DialogueArea
from scenes.fases.explanation_content import get_phase_dialogue_media_for_language
from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel3(BaseExplanationLevel):
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
        bomb_intro_lines = SceneCopyCatalog(
            LanguageService.get().get_current_language()
        ).get("explanation_level3_bomb_intro_lines")
        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if area.name != "dialog_1" or not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            merged_lines = self._dialog_1_base_lines + bomb_intro_lines
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
        return get_phase_dialogue_media_for_language(
            "exp_fase_3",
            LanguageService.get().get_current_language(),
        )
