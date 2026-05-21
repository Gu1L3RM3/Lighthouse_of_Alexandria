from pygame import Surface

from core.managers.language_service import LanguageService
from scenes.fases.explanation_content import get_phase_dialogue_media_for_language
from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel5(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_5",
            next_scene="fase_5",
        )

    def get_dialogue_image_sequences(self) -> dict:
        return get_phase_dialogue_media_for_language(
            "exp_fase_5",
            LanguageService.get().get_current_language(),
        )
