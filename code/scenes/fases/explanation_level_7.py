from pygame import Surface

from scenes.fases.explanation_level import BaseExplanationLevel


class ExplanationLevel7(BaseExplanationLevel):
    def __init__(self, screen: Surface):
        super().__init__(
            screen=screen,
            map_path="exp_fase_7",
            next_scene="home_scene",
        )

    def get_dialogue_image_sequences(self) -> dict[str, list[str]]:
        sequence = [
            "explanations/max_power_transfer_ptbr/01_visao_geral.png",
            "explanations/max_power_transfer_ptbr/02_equivalente_thevenin.png",
            "explanations/max_power_transfer_ptbr/03_condicao_maxima.png",
            "explanations/max_power_transfer_ptbr/04_forma_potencia.png",
            "explanations/max_power_transfer_ptbr/05_passos_vth_rth.png",
            "explanations/max_power_transfer_ptbr/06_exemplo_numerico.png",
            "explanations/max_power_transfer_ptbr/07_eficiencia.png",
            "explanations/max_power_transfer_ptbr/08_gnd_referencia.png",
            "explanations/max_power_transfer_ptbr/08_gnd_referencia.png",
            "explanations/max_power_transfer_ptbr/09_passos_paineis.png",
        ]
        return {"dialog_1": sequence}
