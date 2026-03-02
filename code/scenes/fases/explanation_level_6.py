from pygame import Surface

from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel6(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_6",
            next_scene="fase_6",
        )

    def get_dialogue_image_sequences(self) -> dict[str, list[str]]:
        sequence = [
            "explanations/thevenin_norton_ptbr/01_visao_geral.png",
            "explanations/thevenin_norton_ptbr/02_thevenin_conceito.png",
            "explanations/thevenin_norton_ptbr/03_norton_conceito.png",
            "explanations/thevenin_norton_ptbr/04_relacoes.png",
            "explanations/thevenin_norton_ptbr/05_passos_vth_rth.png",
            "explanations/thevenin_norton_ptbr/06_passos_inorton.png",
            "explanations/thevenin_norton_ptbr/07_exemplo_conversao.png",
            "explanations/thevenin_norton_ptbr/08_gnd_referencia.png",
            "explanations/thevenin_norton_ptbr/08_gnd_referencia.png",
            "explanations/thevenin_norton_ptbr/09_passos_paineis.png",
        ]
        return {"dialog_1": sequence}
