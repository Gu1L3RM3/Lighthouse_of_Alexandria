from pygame import Surface

from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel3(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_3",
            next_scene="fase_3",
        )

    def get_dialogue_image_sequences(self) -> dict[str, list[str]]:
        sequence = [
            "explanations/ohm_law_ptbr/01_visao_geral.png",
            "explanations/ohm_law_ptbr/02_equacoes_ohm.png",
            "explanations/ohm_law_ptbr/03_circuito_basico.png",
            "explanations/ohm_law_ptbr/04_exemplo_corrente.png",
            "explanations/ohm_law_ptbr/05_exemplo_resistencia.png",
            "explanations/ohm_law_ptbr/06_serie_equivalente.png",
            "explanations/ohm_law_ptbr/09_gnd_referencia.png",
            "explanations/ohm_law_ptbr/07_grafico_v_i.png",
            "explanations/ohm_law_ptbr/08_passos_paineis.png",
            "explanations/ohm_law_ptbr/08_passos_paineis.png",
            "explanations/ohm_law_ptbr/08_passos_paineis.png",
        ]
        return {"dialog_1": sequence}
