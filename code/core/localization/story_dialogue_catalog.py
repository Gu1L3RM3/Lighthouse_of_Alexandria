class StoryDialogueCatalog:
    NPC_DIALOGUES = {
        "en": {
            "arquimedes": [
                "Life is like water flowing from a spring.",
            ],
            "father": [
                "Hi son, shall we continue our circuit studies?",
            ],
            "guard": [
                "I need to study for tomorrow's exam.",
            ],
            "professor": [
                "Hello student!",
                "Today we are going to talk about resistors.",
                "Do you know what Ohm's Law is?",
                "It is a very famous law used in many areas of physics and electrical engineering.",
                "But it demands intelligence and dedication to learn it well! Are you willing to gain that knowledge?",
            ],
        },
        "pt-BR": {
            "arquimedes": [
                "A vida e como a agua que sai da nascente",
            ],
            "father": [
                "Oi filho, vamos continuar os estudos de circuitos?",
            ],
            "guard": [
                "Tenho que estudar para a prova de amanha",
            ],
            "professor": [
                "Ola estudante!",
                "Hoje vamos falar sobre resistores.",
                "Voce sabe o que e a Lei de Ohm?",
                "E uma lei muito famosa e utilizada em diversas areas da fisica e da engenharia eletrica.",
                "Mas exige bastante da sua inteligencia e disposicao para aprende-la! Esta disposto a adquirir esse conhecimento?",
            ],
        },
    }

    GENERIC_LEVEL_7 = {
        "en": {
            "arquimedes_hints_with_target": [
                "Archimedes: Kevin... I did not expect this. Is that man really your father?",
                "Kevin: It is him. And he was the one who almost destroyed the Lighthouse to rewrite history.",
                "Archimedes: My God... he almost doomed all of Alexandria.",
                "Kevin: I know. But now he is trapped, and he is still my father.",
                "Archimedes: After everything, do you still want to rescue him?",
                "Kevin: I do. If I do not try, I turn my back on who I am.",
                "Kevin: I will stop his mistake, but I will not abandon my father.",
                "Archimedes: ...All right. Then let us get him out of here and finish this together.",
                "Archimedes: Focus on the target resistor {target}.",
                "Archimedes: Find Thevenin at the load terminals and tune RL to match Rth.",
            ],
            "arquimedes_hints_without_target": [
                "Archimedes: Kevin... I am still in shock. That man is your father.",
                "Kevin: Yes. And I will not let him destroy the Lighthouse.",
                "Archimedes: He almost erased the light of Alexandria...",
                "Kevin: And that is exactly why I need to reach him before it is too late.",
                "Archimedes: I understand. Let us open this cell together.",
                "Archimedes: To do that, use maximum power transfer on the panel.",
                "Archimedes: Find Thevenin at the load terminals and set RL equal to Rth.",
            ],
            "father_dialogue": [
                "Father: Kevin... so you made it this far.",
                "Father: I knew only you would understand the circuits in this place.",
                "Father: This lighthouse is not just a tower.",
                "Father: It is an amplifier of energy... and of history.",
                "Father: At the top lies the Photon Heart.",
                "Father: A core capable of concentrating light, heat... and something far rarer.",
                "Father: Possibilities.",
                "Kevin: Possibilities...?",
                "Father: Every great event in history is born from details almost invisible.",
                "Father: A different wind... an extinguished flame... a lighthouse that stops shining.",
                "Father: I studied records, maps and forgotten accounts.",
                "Father: There is a timeline in which Alexandria is attacked tonight.",
                "Father: An enemy fleet crosses the Mediterranean and reaches the harbor unseen.",
                "Father: Because the lighthouse... was dark.",
                "Father: The city falls.",
                "Father: Thousands die.",
                "Father: But one child escapes in the chaos.",
                "Kevin: A child...?",
                "Father: Years later, she starts a family.",
                "Father: Decades later... you are born because of that.",
                "Kevin: ...my grandmother.",
                "Father: Yes.",
                "Father: In the current timeline, the lighthouse stays lit.",
                "Father: The fleet sees the light from miles away at sea and retreats.",
                "Father: Alexandria is saved.",
                "Father: But that child never escapes... never lives... never comes to exist.",
                "Kevin: So you want to extinguish the lighthouse and doom the whole city?!",
                "Father: I did not choose that price.",
                "Father: I only found the equation.",
                "Father: The Photon Heart allows one critical event to be altered.",
                "Father: If the top of the lighthouse falls, the flame will go out.",
                "Father: Without light... the ships will enter unnoticed.",
                "Father: And history will follow the path where she lives.",
                "Kevin: This is madness.",
                "Father: No.",
                "Father: This is logic.",
                "Father: Now step out of my way.",
                "Father: I need to destroy the top of the lighthouse.",
            ],
            "player_thought": [
                "Kevin: Nooo... he really has gone mad.",
                "Kevin: If I let this happen, Alexandria will be destroyed.",
                "Kevin: I will stop my father, no matter the cost.",
            ],
        },
        "pt-BR": {
            "arquimedes_hints_with_target": [
                "Arquimedes: Kevin... eu nao esperava isso. Aquele homem e mesmo seu pai?",
                "Kevin: E ele. E foi ele quem quase destruiu o Farol para mudar a historia.",
                "Arquimedes: Meu Deus... ele quase condenou Alexandria inteira.",
                "Kevin: Eu sei. Mas agora ele esta preso e ainda e meu pai.",
                "Arquimedes: Depois de tudo isso, voce ainda quer resgata-lo?",
                "Kevin: Quero. Se eu nao tentar, eu viro as costas para quem eu sou.",
                "Kevin: Eu vou impedir o erro dele, mas nao vou abandonar meu pai.",
                "Arquimedes: ...Certo. Entao vamos tira-lo daqui e terminar isso juntos.",
                "Arquimedes: Foque no resistor alvo {target}.",
                "Arquimedes: Encontre Thevenin nos terminais da carga e ajuste RL para casar com Rth.",
            ],
            "arquimedes_hints_without_target": [
                "Arquimedes: Kevin... eu ainda estou em choque. Aquele homem e seu pai.",
                "Kevin: Sim. E eu nao vou deixar ele destruir o Farol.",
                "Arquimedes: Ele quase apagou a luz de Alexandria...",
                "Kevin: E por isso mesmo eu preciso chegar nele antes que seja tarde.",
                "Arquimedes: Entendi. Vamos abrir essa cela juntos.",
                "Arquimedes: Para isso, use maxima transferencia de potencia no painel.",
                "Arquimedes: Ache Thevenin nos terminais da carga e ajuste RL para ficar igual a Rth.",
            ],
            "father_dialogue": [
                "Pai: Kevin... entao voce chegou ate aqui.",
                "Pai: Eu sabia que apenas voce entenderia os circuitos deste lugar.",
                "Pai: Este farol nao e apenas uma torre.",
                "Pai: Ele e um amplificador de energia... e de historia.",
                "Pai: No topo esta o Coracao de Foton.",
                "Pai: Um nucleo capaz de concentrar luz, calor... e algo muito mais raro.",
                "Pai: Possibilidades.",
                "Kevin: Possibilidades...?",
                "Pai: Cada grande evento da historia nasce de detalhes quase invisiveis.",
                "Pai: Um vento diferente... uma chama apagada... um farol que deixa de brilhar.",
                "Pai: Eu estudei registros, mapas e relatos esquecidos.",
                "Pai: Existe uma linha do tempo em que Alexandria foi atacada nesta noite.",
                "Pai: Uma frota inimiga cruza o Mediterraneo e alcanca o porto sem ser vista.",
                "Pai: Porque o farol... estava apagado.",
                "Pai: A cidade cai.",
                "Pai: Milhares morrem.",
                "Pai: Mas uma crianca escapa no caos.",
                "Kevin: Uma crianca...?",
                "Pai: Anos depois, ela forma uma familia.",
                "Pai: Decadas depois... voce nasce por causa disso.",
                "Kevin: ...minha avo.",
                "Pai: Sim.",
                "Pai: Na linha do tempo atual, o farol permanece aceso.",
                "Pai: A frota ve a luz a quilometros no mar e recua.",
                "Pai: Alexandria e salva.",
                "Pai: Mas aquela crianca nunca foge... nunca vive... nunca chega a existir.",
                "Kevin: Entao voce quer apagar o farol para condenar a cidade inteira?!",
                "Pai: Eu nao escolhi esse preco.",
                "Pai: Eu apenas encontrei a equacao.",
                "Pai: O Coracao de Foton permite alterar um unico evento critico.",
                "Pai: Se o topo do farol cair, a chama se apagara.",
                "Pai: Sem luz... os navios entrarao sem serem percebidos.",
                "Pai: E a historia seguira o caminho em que ela vive.",
                "Kevin: Isso e loucura.",
                "Pai: Nao.",
                "Pai: Isso e logica.",
                "Pai: Agora saia do meu caminho.",
                "Pai: Eu preciso destruir o topo do farol.",
            ],
            "player_thought": [
                "Kevin: Naoo... ele realmente enlouqueceu.",
                "Kevin: Se eu deixar isso acontecer, Alexandria sera destruida.",
                "Kevin: Eu vou impedir meu pai, custe o que custar.",
            ],
        },
    }

    GENERIC_LEVEL_PANEL_HINTS = {
        "en": {
            "level3_voltage": "Archimedes: To activate panel {panel_id}, the resistor in the circuit must have a voltage close to {value}.",
            "level3_power": "Archimedes: To activate panel {panel_id}, the resistor in the circuit must have power close to {value}.",
            "level3_current": "Archimedes: To activate panel {panel_id}, the resistor in the circuit must have current close to {value}.",
            "level5_voltage": "Archimedes: To activate panel {panel_id}, the voltages should be approximately: {parts}",
            "level5_current": "Archimedes: To activate panel {panel_id}, the currents should be approximately: {parts}",
            "level6_thevenin": "Archimedes: Panel {panel_id}: isolate the terminals of R1, calculate Vth and Rth, and build the equivalent with a voltage source in series with a resistance. Extra hint: turn off the independent sources to find the equivalent resistance.",
            "level6_norton": "Archimedes: Panel {panel_id}: isolate the terminals of R1, calculate In and Rn, and build the equivalent with a current source in parallel with a resistance. Extra hint: turn off the independent sources to find the equivalent resistance.",
        },
        "pt-BR": {
            "level3_voltage": "Arquimedes: Para ativar o painel {panel_id} o resistor do circuito deve ter tensao proxima de {value}.",
            "level3_power": "Arquimedes: Para ativar o painel {panel_id} o resistor do circuito deve ter potencia proxima de {value}.",
            "level3_current": "Arquimedes: Para ativar o painel {panel_id} o resistor do circuito deve ter corrente proxima de {value}.",
            "level5_voltage": "Arquimedes: Para ativar o painel {panel_id}, as tensoes devem ser aproximadamente: {parts}",
            "level5_current": "Arquimedes: Para ativar o painel {panel_id}, as correntes devem ser aproximadamente: {parts}",
            "level6_thevenin": "Arquimedes: Painel {panel_id}: isole os terminais de R1, calcule Vth e Rth e monte o equivalente com fonte de tensao em serie com resistencia. Dica extra: desligue as fontes independentes para achar a resistencia equivalente.",
            "level6_norton": "Arquimedes: Painel {panel_id}: isole os terminais de R1, calcule In e Rn e monte o equivalente com fonte de corrente em paralelo com resistencia. Dica extra: desligue as fontes independentes para achar a resistencia equivalente.",
        },
    }

    FINAL_LEVEL_INTRO = {
        "en": [
            "Archimedes: Kevin, your father ran to the top with the Photon Heart.",
            "Archimedes: He wants to extinguish the lighthouse to force your grandmother's timeline.",
            "Archimedes: This room is the final seal. There are four active panels at the same time.",
            "Archimedes: Each solved panel lasts only a short while. If time runs out, it resets.",
            "Archimedes: Tip: on each panel, focus on target resistor R1 and aim for maximum transfer.",
            "Archimedes: First find the Thevenin equivalent at the load terminals.",
            "Archimedes: Key rule: for maximum power, adjust RL so it is approximately equal to Rth.",
            "Archimedes: The panel checks power and resistance. Confirm both before you finish.",
            "Archimedes: Strategy: leave components near the panels and solve them in sequence without stopping.",
            "Archimedes: If we fail here, Alexandria falls before dawn.",
        ],
        "pt-BR": [
            "Arquimedes: Kevin, seu pai correu para o topo com o Coracao de Foton.",
            "Arquimedes: Ele quer apagar o farol para forcar a linha do tempo da sua avo.",
            "Arquimedes: Esta sala e o ultimo selo. Sao quatro paineis ativos ao mesmo tempo.",
            "Arquimedes: Cada painel resolvido dura pouco. Se o tempo acabar, ele reinicia.",
            "Arquimedes: Dica: em cada painel, foque no resistor alvo R1 e busque maxima transferencia.",
            "Arquimedes: Primeiro encontre o equivalente de Thevenin nos terminais da carga.",
            "Arquimedes: Regra-chave: para maxima potencia, ajuste RL para ficar aproximadamente igual a Rth.",
            "Arquimedes: O painel cobra potencia e resistencia. Confira os dois antes de fechar.",
            "Arquimedes: Estrategia: deixe componentes perto dos paineis e resolva em sequencia sem parar.",
            "Arquimedes: Se falharmos aqui, Alexandria cai antes do amanhecer.",
        ],
    }

    def __init__(self, language: str = "en"):
        self.language = language if language in ("en", "pt-BR") else "en"

    def get_npc_dialogue(self, npc_key: str) -> list[str]:
        return list(self.NPC_DIALOGUES[self.language][npc_key])

    def get_generic_level_7_arquimedes_hints(self, target: str | None = None) -> list[str]:
        key = "arquimedes_hints_with_target" if target else "arquimedes_hints_without_target"
        lines = list(self.GENERIC_LEVEL_7[self.language][key])
        if target:
            lines = [line.format(target=target) for line in lines]
        return lines

    def get_generic_level_7_father_dialogue(self) -> list[str]:
        return list(self.GENERIC_LEVEL_7[self.language]["father_dialogue"])

    def get_generic_level_7_player_thought_dialogue(self) -> list[str]:
        return list(self.GENERIC_LEVEL_7[self.language]["player_thought"])

    def get_level3_panel_hint(self, panel_id: int, solution_type: str, value: str) -> str:
        key = {
            "voltage": "level3_voltage",
            "power": "level3_power",
            "current": "level3_current",
        }[solution_type]
        return self.GENERIC_LEVEL_PANEL_HINTS[self.language][key].format(panel_id=panel_id, value=value)

    def get_level5_panel_hint(self, panel_id: int, solution_type: str, parts: str) -> str:
        key = {
            "voltage": "level5_voltage",
            "current": "level5_current",
        }[solution_type]
        return self.GENERIC_LEVEL_PANEL_HINTS[self.language][key].format(panel_id=panel_id, parts=parts)

    def get_level6_panel_hint(self, panel_id: int, mode: str) -> str:
        key = "level6_thevenin" if mode == "thevenin" else "level6_norton"
        return self.GENERIC_LEVEL_PANEL_HINTS[self.language][key].format(panel_id=panel_id)

    def get_final_level_intro(self) -> list[str]:
        return list(self.FINAL_LEVEL_INTRO[self.language])
