from pygame import Surface

from scenes.fases.explanation_content import get_phase_dialogue_media
from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel3(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_3",
            next_scene="fase_3",
        )

    def get_dialogue_image_sequences(self) -> dict:
        return get_phase_dialogue_media("exp_fase_3")
