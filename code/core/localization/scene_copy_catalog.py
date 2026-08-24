from pathlib import Path

from core.settings import ASSETS_DIR


class SceneCopyCatalog:
    SCENE_COPY = {
        "en": {
            "credits_title": "CREDITS",
            "credits_subtitle": "Project references and attributions",
            "credits_back_button": "BACK TO MENU",
            "credits_back_hint": "Controller: press B to return to menu",
            "credits_lines": [
                "Project",
                "Lighthouse of Alexandria",
                "",
                "Author",
                "Guilherme Abreu Cavazzani",
                "",
                "Advisor",
                "Samir Martins",
                "",
                "Institution and group",
                "Project developed at GCoM",
                "https://www.ufsj.edu.br/gcom/",
                "",
                "Asset and library credits",
                "Top Down Adventure Pack v1.0 - o_lobster",
                "https://o-lobster.itch.io/adventure-pack",
                "2D Pixel Dungeon Asset Pack v2.0",
                "Used for tiles and visual elements in the game",
                "NumPy (numerical Modified Nodal Analysis)",
                "https://numpy.org/",
                "Font: PressStart2P-Regular.ttf",
                "License follows the original font distribution",
                "",
                "NOTICE",
                "Selling this game is not allowed without the author's permission.",
            ],
            "ending_title": "LIGHTHOUSE OF ALEXANDRIA",
            "ending_subtitle": "Thanks and final credits",
            "ending_lines": [
                "THANK YOU",
                "Thank you for playing Lighthouse of Alexandria.",
                "",
                "CREDITS",
                "Author: Guilherme Abreu Cavazzani",
                "Advisor: Samir Martins",
                "Project developed at GCoM",
                "https://www.ufsj.edu.br/gcom/",
                "",
                "Assets and libraries:",
                "Top Down Adventure Pack v1.0 - o_lobster",
                "2D Pixel Dungeon Asset Pack v2.0",
                "NumPy (numerical Modified Nodal Analysis)",
                "Font: PressStart2P-Regular.ttf",
                "",
                "Selling this game is not allowed without the author's permission.",
            ],
            "ending_skip_hint": "{confirm}/{back} to skip",
            "lighthouse_title": "THE LIGHT OF THE LIGHTHOUSE RETURNS",
            "lighthouse_subtitle": "Alexandria can see the horizon once more.",
            "lighthouse_skip_hint": "{confirm} to skip",
            "death_retry_title": "ATTEMPT LOST",
            "death_retry_subtitle": "Take a breath and try again.",
            "death_game_over_subtitle": "The shadows win for now; we return to the start of the journey to try once more.",
            "death_lives_label": "ATTEMPTS",
            "death_advance_hint": "{confirm} to continue",
            "dialog_continue": "continue",
            "lives_label": "ATTEMPTS",
            "confirm_yes": "YES",
            "confirm_no": "NO",
            "clear_circuit_title": "CLEAR THE ENTIRE CIRCUIT?",
            "save_exit_title": "SAVE AND EXIT?",
            "explanation_level3_bomb_intro_lines": [
                "Archimedes: Kevin, before stage 3 you will use photon charges, not ordinary explosives.",
                "Archimedes: They release a short pulse that destabilizes the shadows and opens a path through the panels.",
                "Archimedes: The pulse depends on the CORE; if the calibration is poor, the effect weakens.",
                "Archimedes: In the field, press B to place the charge and use the CORE button to adjust it on the panel.",
                "Archimedes: Use them strategically. Every charge must count until we light the lighthouse path.",
            ],
        },
        "pt-BR": {
            "credits_title": "CREDITOS",
            "credits_subtitle": "Referencias e atribuicoes do projeto",
            "credits_back_button": "VOLTAR AO MENU",
            "credits_back_hint": "Controle: aperte B para voltar ao menu",
            "credits_lines": [
                "Projeto",
                "Farol de Alexandria",
                "",
                "Autor",
                "Guilherme Abreu Cavazzani",
                "",
                "Orientador",
                "Samir Martins",
                "",
                "Instituicao e grupo",
                "Projeto desenvolvido no GCoM",
                "https://www.ufsj.edu.br/gcom/",
                "",
                "Creditos de assets e bibliotecas",
                "Top Down Adventure Pack v1.0 - o_lobster",
                "https://o-lobster.itch.io/adventure-pack",
                "2D Pixel Dungeon Asset Pack v2.0",
                "Usado em tiles e elementos visuais do jogo",
                "NumPy (Analise Nodal Modificada numerica)",
                "https://numpy.org/",
                "Fonte: PressStart2P-Regular.ttf",
                "Licenca conforme distribuicao original da fonte",
                "",
                "AVISO",
                "Nao e permitido vender este jogo sem autorizacao do autor.",
            ],
            "ending_title": "FAROL DE ALEXANDRIA",
            "ending_subtitle": "Agradecimentos e creditos finais",
            "ending_lines": [
                "AGRADECIMENTOS",
                "Obrigado por jogar Farol de Alexandria.",
                "",
                "CREDITOS",
                "Autor: Guilherme Abreu Cavazzani",
                "Orientador: Samir Martins",
                "Projeto desenvolvido no GCoM",
                "https://www.ufsj.edu.br/gcom/",
                "",
                "Assets e bibliotecas:",
                "Top Down Adventure Pack v1.0 - o_lobster",
                "2D Pixel Dungeon Asset Pack v2.0",
                "NumPy (Analise Nodal Modificada numerica)",
                "Fonte: PressStart2P-Regular.ttf",
                "",
                "Nao e permitido vender este jogo sem autorizacao do autor.",
            ],
            "ending_skip_hint": "{confirm}/{back} para pular",
            "lighthouse_title": "A LUZ DO FAROL RENASCE",
            "lighthouse_subtitle": "Alexandria volta a enxergar o horizonte.",
            "lighthouse_skip_hint": "{confirm} para pular",
            "death_retry_title": "TENTATIVA PERDIDA",
            "death_retry_subtitle": "Respire e tente novamente.",
            "death_game_over_subtitle": "As sombras vencem por ora; voltamos ao inicio da jornada para tentar de novo.",
            "death_lives_label": "TENTATIVAS",
            "death_advance_hint": "{confirm} para avancar",
            "dialog_continue": "continuar",
            "lives_label": "TENTATIVAS",
            "confirm_yes": "SIM",
            "confirm_no": "NAO",
            "clear_circuit_title": "LIMPAR TODO O CIRCUITO?",
            "save_exit_title": "SALVAR E SAIR?",
            "explanation_level3_bomb_intro_lines": [
                "Arquimedes: Kevin, antes da fase 3 voce vai usar cargas de foton, nao explosivos comuns.",
                "Arquimedes: Elas liberam um pulso curto que desestabiliza as sombras e abre passagem nos paineis.",
                "Arquimedes: O pulso depende do NUCLEO; se a calibracao estiver ruim, o efeito cai.",
                "Arquimedes: Em campo, pressione B para posicionar a carga e use o botao NUCLEO para ajustar no painel.",
                "Arquimedes: Use com estrategia. Cada carga precisa contar ate acendermos o caminho do farol.",
            ],
        },
    }

    EXPLANATION_CAPTIONS = {
        "en": {
            "exp_fase_3": {
                "dialog_1": [
                    "Ohm's Law: overview of the basic concepts.",
                    "Basic circuit with source, resistor and current.",
                    "Main relation: V = R x I.",
                    "Electric power: base equation P = V x I.",
                    "Equations with resistance: P = I^2 x R and P = V^2 / R.",
                    "Resistor example: R = 6 ohms, V = 12 V, P = 24 W.",
                    "Series association: how to find Req.",
                    "GND defines the 0 V reference.",
                    "Without GND, measurements may become incorrect.",
                    "Panels can ask for voltage, current or power.",
                    "Step by step to solve the panels in stage 3.",
                ]
            },
            "exp_fase_4": {
                "dialog_1": [
                    "Resistor association: goal of this stage.",
                    "Series: equivalent resistance formula.",
                    "Series association example.",
                    "Parallel: inverse-sum formula.",
                    "Parallel association example.",
                    "Mixed circuit: block reduction.",
                    "Voltage divider in series.",
                    "GND as the mandatory voltage reference.",
                    "Without GND, the circuit may become inconsistent.",
                    "Recommended sequence to solve the panels.",
                ]
            },
            "exp_fase_5": {
                "dialog_1": [
                    "Node method with Kirchhoff: general overview.",
                    "KCL: current entering and leaving each node.",
                    "Building the nodal equation.",
                    "Practical steps to assemble the node system.",
                    "KVL: sum of voltages in a closed loop.",
                    "Solved numerical example.",
                    "GND defines the reference potential.",
                    "Without GND, results can be wrong.",
                    "Checklist to solve the stage panels.",
                ]
            },
            "exp_fase_6": {
                "dialog_1": [
                    "Thevenin and Norton theorems: general overview.",
                    "Thevenin: voltage source in series with Rth.",
                    "Norton: current source in parallel with Rn.",
                    "Relations among Vth, In, Rth and Rn.",
                    "How to obtain Vth with the load removed.",
                    "How to obtain Rth from the circuit terminals.",
                    "How to obtain In by short-circuiting the terminals.",
                    "Proper use of GND during measurements.",
                    "Without GND, the equivalent may remain undefined.",
                    "Final procedure for the panels.",
                ]
            },
            "exp_fase_7": {
                "dialog_1": [
                    "Maximum power transfer: stage objective.",
                    "Circuit seen by the load in Thevenin equivalent form.",
                    "Maximum power condition: RL approximately equal to Rth.",
                    "Mathematical form of power as a function of RL.",
                    "Steps to find Vth and Rth.",
                    "Worked example with numerical values.",
                    "Efficiency under maximum transfer condition.",
                    "GND avoids ambiguity in measurements.",
                    "Validating the solution on the panels.",
                    "Choosing the best RL option on the panel.",
                ]
            },
        },
        "pt-BR": {},
    }

    def __init__(self, language: str = "en"):
        self.language = language if language in ("en", "pt-BR") else "en"

    def get(self, key: str):
        return self.SCENE_COPY[self.language][key]

    def get_explanation_captions(self, map_path: str, dialogue_name: str) -> list[str] | None:
        by_language = self.EXPLANATION_CAPTIONS.get(self.language, {})
        by_map = by_language.get(map_path, {})
        captions = by_map.get(dialogue_name)
        if captions is None and self.language != "pt-BR":
            return None
        return list(captions) if captions is not None else None


def resolve_explanation_image_path(relative_path: str, language: str) -> str:
    if language == "pt-BR":
        return relative_path

    english_candidate = relative_path.replace("_ptbr/", "_en/", 1)
    full_candidate = Path(ASSETS_DIR) / "images" / english_candidate
    if full_candidate.exists():
        return english_candidate
    return relative_path
