from pygame import Surface

from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel4(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_4",
            next_scene="fase_4",
        )

    def get_dialogue_image_sequences(self) -> dict[str, list[str]]:
        sequence = [
            "explanations/resistor_assoc_ptbr/01_visao_geral.png",
            "explanations/resistor_assoc_ptbr/02_serie_formula.png",
            "explanations/resistor_assoc_ptbr/03_serie_exemplo.png",
            "explanations/resistor_assoc_ptbr/04_paralelo_formula.png",
            "explanations/resistor_assoc_ptbr/05_paralelo_exemplo.png",
            "explanations/resistor_assoc_ptbr/06_misto_blocos.png",
            "explanations/resistor_assoc_ptbr/07_divisor_tensao.png",
            "explanations/resistor_assoc_ptbr/08_gnd_referencia.png",
            "explanations/resistor_assoc_ptbr/08_gnd_referencia.png",
            "explanations/resistor_assoc_ptbr/09_passos_paineis.png",
        ]
        return {"dialog_1": sequence}
