from __future__ import annotations


EXPLANATION_CONTENT: dict[str, dict[str, dict[str, list[str]]]] = {
    "exp_fase_3": {
        "dialog_1": {
            "images": [
                "explanations/ohm_law_ptbr/01_visao_geral.png",
                "explanations/ohm_law_ptbr/03_circuito_basico.png",
                "explanations/ohm_law_ptbr/02_equacoes_ohm.png",
                "explanations/ohm_law_ptbr/04_exemplo_corrente.png",
                "explanations/ohm_law_ptbr/05_exemplo_resistencia.png",
                "explanations/ohm_law_ptbr/06_serie_equivalente.png",
                "explanations/ohm_law_ptbr/09_gnd_referencia.png",
                "explanations/ohm_law_ptbr/09_gnd_referencia.png",
                "explanations/ohm_law_ptbr/07_grafico_v_i.png",
                "explanations/ohm_law_ptbr/07_grafico_v_i.png",
                "explanations/ohm_law_ptbr/08_passos_paineis.png",
            ],
            "captions": [
                "Lei de Ohm: visão geral dos conceitos básicos.",
                "Circuito básico com fonte, resistor e corrente.",
                "Relação principal: V = R x I.",
                "Exemplo prático para achar corrente (I = V / R).",
                "Exemplo prático para achar resistência (R = V / I).",
                "Associação em série: como obter Req.",
                "GND define a referência de 0 V.",
                "Sem GND, medidas podem ficar incorretas.",
                "Gráfico V x I em resistor ôhmico.",
                "Maior inclinação da reta implica maior resistência.",
                "Passo a passo para resolver os painéis da fase.",
            ],
        }
    },
    "exp_fase_4": {
        "dialog_1": {
            "images": [
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
            ],
            "captions": [
                "Associação de resistores: objetivo da etapa.",
                "Série: fórmula da resistência equivalente.",
                "Exemplo de associação em série.",
                "Paralelo: fórmula pela soma dos inversos.",
                "Exemplo de associação em paralelo.",
                "Circuito misto: redução por blocos.",
                "Divisor de tensão em série.",
                "GND como referência obrigatória de tensão.",
                "Sem GND, o circuito pode ficar inconsistente.",
                "Sequência recomendada para resolver os painéis.",
            ],
        }
    },
    "exp_fase_5": {
        "dialog_1": {
            "images": [
                "explanations/nodal_kirchhoff_ptbr/01_visao_geral.png",
                "explanations/nodal_kirchhoff_ptbr/02_kcl_conceito.png",
                "explanations/nodal_kirchhoff_ptbr/03_kcl_equacao_no.png",
                "explanations/nodal_kirchhoff_ptbr/05_passos_metodo_nos.png",
                "explanations/nodal_kirchhoff_ptbr/04_kvl_malha.png",
                "explanations/nodal_kirchhoff_ptbr/06_exemplo_numerico.png",
                "explanations/nodal_kirchhoff_ptbr/07_gnd_referencia.png",
                "explanations/nodal_kirchhoff_ptbr/07_gnd_referencia.png",
                "explanations/nodal_kirchhoff_ptbr/08_passos_paineis.png",
            ],
            "captions": [
                "Método dos nós com Kirchhoff: panorama geral.",
                "KCL: corrente que entra e sai de cada nó.",
                "Montagem da equação nodal.",
                "Passos práticos para montar o sistema de nós.",
                "KVL: soma das tensões em malha fechada.",
                "Exemplo numérico resolvido.",
                "GND define o potencial de referência.",
                "Sem GND, os resultados podem sair errados.",
                "Checklist para resolver os painéis da fase.",
            ],
        }
    },
    "exp_fase_6": {
        "dialog_1": {
            "images": [
                "explanations/thevenin_norton_ptbr/01_visao_geral.png",
                "explanations/thevenin_norton_ptbr/02_thevenin_conceito.png",
                "explanations/thevenin_norton_ptbr/03_norton_conceito.png",
                "explanations/thevenin_norton_ptbr/04_relacoes.png",
                "explanations/thevenin_norton_ptbr/05_passos_vth_rth.png",
                "explanations/thevenin_norton_ptbr/05_passos_vth_rth.png",
                "explanations/thevenin_norton_ptbr/06_passos_inorton.png",
                "explanations/thevenin_norton_ptbr/08_gnd_referencia.png",
                "explanations/thevenin_norton_ptbr/08_gnd_referencia.png",
                "explanations/thevenin_norton_ptbr/09_passos_paineis.png",
            ],
            "captions": [
                "Teoremas de Thévenin e Norton: visão geral.",
                "Thévenin: fonte de tensão em série com Rth.",
                "Norton: fonte de corrente em paralelo com Rn.",
                "Relações entre Vth, In, Rth e Rn.",
                "Como obter Vth com carga removida.",
                "Como obter Rth pelos terminais do circuito.",
                "Como obter In por curto-circuito nos terminais.",
                "Uso correto de GND nas medições.",
                "Sem GND, o equivalente pode ficar indefinido.",
                "Procedimento final para os painéis.",
            ],
        }
    },
    "exp_fase_7": {
        "dialog_1": {
            "images": [
                "explanations/max_power_transfer_ptbr/01_visao_geral.png",
                "explanations/max_power_transfer_ptbr/02_equivalente_thevenin.png",
                "explanations/max_power_transfer_ptbr/03_condicao_maxima.png",
                "explanations/max_power_transfer_ptbr/04_forma_potencia.png",
                "explanations/max_power_transfer_ptbr/05_passos_vth_rth.png",
                "explanations/max_power_transfer_ptbr/06_exemplo_numerico.png",
                "explanations/max_power_transfer_ptbr/07_eficiencia.png",
                "explanations/max_power_transfer_ptbr/08_gnd_referencia.png",
                "explanations/max_power_transfer_ptbr/09_passos_paineis.png",
                "explanations/max_power_transfer_ptbr/09_passos_paineis.png",
            ],
            "captions": [
                "Máxima transferência de potência: objetivo da fase.",
                "Circuito visto pela carga no equivalente de Thévenin.",
                "Condição de máxima potência: RL aproximadamente igual a Rth.",
                "Forma matemática da potência em função de RL.",
                "Passos para achar Vth e Rth.",
                "Exemplo de cálculo com valores numéricos.",
                "Eficiência na condição de máxima transferência.",
                "GND evita ambiguidades de medição.",
                "Validação da solução nos painéis.",
                "Escolha da melhor opção de RL no painel.",
            ],
        }
    },
}


def get_phase_dialogue_media(map_path: str) -> dict[str, dict[str, list[str]]]:
    return EXPLANATION_CONTENT.get(map_path, {})