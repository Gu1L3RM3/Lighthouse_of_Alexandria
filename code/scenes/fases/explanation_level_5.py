from pygame import Surface

from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel5(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_5",
            next_scene="fase_5",
        )

    def get_dialogue_image_sequences(self) -> dict[str, list[str]]:
        sequence = [
            "explanations/nodal_kirchhoff_ptbr/01_visao_geral.png",
            "explanations/nodal_kirchhoff_ptbr/02_kcl_conceito.png",
            "explanations/nodal_kirchhoff_ptbr/03_kcl_equacao_no.png",
            "explanations/nodal_kirchhoff_ptbr/05_passos_metodo_nos.png",
            "explanations/nodal_kirchhoff_ptbr/04_kvl_malha.png",
            "explanations/nodal_kirchhoff_ptbr/06_exemplo_numerico.png",
            "explanations/nodal_kirchhoff_ptbr/07_gnd_referencia.png",
            "explanations/nodal_kirchhoff_ptbr/07_gnd_referencia.png",
            "explanations/nodal_kirchhoff_ptbr/08_passos_paineis.png",
        ]
        return {"dialog_1": sequence}
