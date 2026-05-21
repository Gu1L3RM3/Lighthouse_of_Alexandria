HELP_PAGE_COPY = {
    "en": {
        "title": "HELP - HOW TO PLAY",
        "subtitle": "Movement, shortcuts and circuit editor",
        "intro": "Quick guide to the Lighthouse of Alexandria",
    },
    "pt-BR": {
        "title": "HELP - COMO JOGAR",
        "subtitle": "Movimento, atalhos e editor de circuito",
        "intro": "Guia rapido do Farol de Alexandria",
    },
}

HELP_SECTIONS_BY_LANGUAGE: dict[str, list[dict[str, list[str] | str]]] = {
    "en": [
        {
            "title": "Basic Controls",
            "lines": [
                "Keyboard: W A S D moves the character. Controller: left stick or D-Pad.",
                "Keyboard: E interacts with doors, panels and nearby objects. Controller: A.",
                "Keyboard: B places a bomb in stages that use cores. Controller: X.",
                "Keyboard: Esc opens the menu. Controller: Start.",
                "L: toggles the stage light on and off.",
            ],
        },
        {
            "title": "Game Objective",
            "lines": [
                "Explore the map, read the dialogues and solve the electrical challenges.",
                "Each panel needs the correct circuit to unlock doors, lights or progress.",
                "Use items collected on the map to assemble the right circuit in the editor.",
            ],
        },
        {
            "title": "How To Open the Circuit Editor",
            "lines": [
                "Move close to a control panel and press E on keyboard or A on controller.",
                "In the bomb challenge, use the CORE button in the stage UI or Y on controller.",
                "When the editor opens, build the circuit and click Solve to validate it.",
            ],
        },
        {
            "title": "Editor: Top Bar (Buttons)",
            "lines": [
                "Node: adds a connection node.",
                "V Source: adds a voltage source (opens the available values list).",
                "Resistor: adds a resistor (opens the available values list).",
                "I Source: adds a current source (opens the available values list).",
                "GND: adds ground (required reference in many circuits).",
                "Wire: adds a wire to connect components.",
                "X: saves and closes the editor.",
            ],
        },
        {
            "title": "Editor: Side Bar (Buttons)",
            "lines": [
                "R: rotation tool for the selected component.",
                "D: delete tool.",
                "S: selection tool.",
                "Solve: saves the current circuit, generates the netlist and solves the circuit.",
                "Load: loads the circuit saved in the current file.",
                "Clear: removes editable components.",
            ],
        },
        {
            "title": "Controller Editor Shortcuts",
            "lines": [
                "Left stick / D-Pad: moves focus across the grid.",
                "A: applies the action on the grid (place, select or edit depending on the active tool).",
                "Y: rotates the current brush when a component is selected.",
                "B: cancels the current brush (same as Esc on keyboard).",
                "LB/RB: moves between editor menu buttons.",
                "L3: confirms or clicks the currently focused menu button.",
            ],
        },
        {
            "title": "Editor: What S, B and D Mean",
            "lines": [
                "S (side bar button): Select. Lets you select a circuit component to reposition it.",
                "D (side bar button): Delete. Removes editable components from the circuit.",
                "B (controller button): Back/Cancel. Leaves the current tool without closing the editor.",
            ],
        },
        {
            "title": "Editor: Keyboard Shortcuts",
            "lines": [
                "N: select Node.",
                "W: select Wire.",
                "G: select GND.",
                "R: rotate the current component.",
                "S: select the Select tool.",
                "Delete: select the Delete tool.",
                "Esc: cancel the current tool.",
            ],
        },
        {
            "title": "Editor: Component Lists (Resistor, V Source, I Source)",
            "lines": [
                "Lists can be scrolled with the mouse wheel.",
                "The arrow up/down shortcuts also work.",
                "PageUp and PageDown scroll faster.",
                "Home jumps to the top of the list and End goes to the bottom.",
            ],
        },
        {
            "title": "Recommended Editor Flow",
            "lines": [
                "1) Place GND and the main nodes.",
                "2) Add sources and resistors with the correct values.",
                "3) Connect everything with Wire.",
                "4) Adjust orientations with R and remove mistakes with D.",
                "5) Click Solve to validate the results.",
                "6) Leave through X when you are done.",
            ],
        },
    ],
    "pt-BR": [
        {
            "title": "Controles Basicos",
            "lines": [
                "Teclado: W A S D movimenta o personagem. Controle: analogico esquerdo ou D-Pad.",
                "Teclado: E interage com portas, paineis e objetos proximos. Controle: A.",
                "Teclado: B posiciona bomba nas fases que usam nucleos. Controle: X.",
                "Teclado: Esc abre o menu. Controle: Start.",
                "L: alterna a luz da fase (acende/apaga).",
            ],
        },
        {
            "title": "Objetivo do Jogo",
            "lines": [
                "Explore o mapa, leia os dialogos e resolva os desafios eletricos.",
                "Cada painel exige um circuito correto para liberar portas, luzes ou progresso.",
                "Use os itens coletados no mapa para montar o circuito correto no editor.",
            ],
        },
        {
            "title": "Como Abrir o Editor de Circuito",
            "lines": [
                "Aproxime-se de um painel de controle e pressione E no teclado ou A no controle.",
                "No desafio da bomba, use o botao NUCLEO na interface da fase ou Y no controle.",
                "Ao abrir o editor, monte o circuito e clique em Solve para validar.",
            ],
        },
        {
            "title": "Editor: Barra Superior (Botoes)",
            "lines": [
                "Node: adiciona um no de conexao.",
                "V Source: adiciona fonte de tensao (abre lista de valores disponiveis).",
                "Resistor: adiciona resistor (abre lista de valores disponiveis).",
                "I Source: adiciona fonte de corrente (abre lista de valores disponiveis).",
                "GND: adiciona o terra (referencia obrigatoria em varios circuitos).",
                "Wire: adiciona fio para conectar os componentes.",
                "X: salva e fecha o editor.",
            ],
        },
        {
            "title": "Editor: Barra Lateral (Botoes)",
            "lines": [
                "R: ferramenta de rotacao do componente selecionado.",
                "D: ferramenta de exclusao.",
                "S: ferramenta de selecao.",
                "Solve: salva o circuito atual, gera a netlist e resolve o circuito.",
                "Load: carrega o circuito salvo no arquivo atual.",
                "Clear: limpa os componentes editaveis.",
            ],
        },
        {
            "title": "Editor no Controle (Resumo Rapido)",
            "lines": [
                "Analagico esquerdo / D-Pad: move o foco no grid.",
                "A: aplica acao no grid (colocar, selecionar ou editar conforme a ferramenta ativa).",
                "Y: gira o brush atual quando houver um componente em uso.",
                "B: cancela o brush atual (equivalente ao Esc no teclado).",
                "LB/RB: navega entre os botoes do menu do editor.",
                "L3: confirma/clica no botao do menu que esta focado.",
            ],
        },
        {
            "title": "Editor: O que significam S, B e D",
            "lines": [
                "S (botao da barra lateral): Select. Permite selecionar um componente do circuito para reposicionar.",
                "D (botao da barra lateral): Delete. Remove componentes editaveis do circuito.",
                "B (botao do controle): Back/Cancelar. Sai da ferramenta atual sem fechar o editor.",
            ],
        },
        {
            "title": "Editor: Atalhos de Teclado",
            "lines": [
                "N: selecionar Node.",
                "W: selecionar Wire.",
                "G: selecionar GND.",
                "R: rotacionar o componente em uso.",
                "S: selecionar ferramenta Select.",
                "Delete: selecionar ferramenta Delete.",
                "Esc: cancelar ferramenta atual.",
            ],
        },
        {
            "title": "Editor: Listas de Componentes (Resistor, V Source, I Source)",
            "lines": [
                "As listas podem ser roladas com a roda do mouse.",
                "Tambem funcionam os atalhos: seta para cima/baixo.",
                "PageUp e PageDown rolam mais rapido.",
                "Home vai para o topo da lista e End vai para o final.",
            ],
        },
        {
            "title": "Fluxo Recomendado no Editor",
            "lines": [
                "1) Coloque o GND e os nos principais.",
                "2) Adicione fontes e resistores com valores corretos.",
                "3) Conecte tudo com Wire.",
                "4) Ajuste orientacoes com R e remova erros com D.",
                "5) Clique em Solve para validar os resultados.",
                "6) Saia pelo X quando terminar.",
            ],
        },
    ],
}


def get_help_sections(language: str) -> list[dict[str, list[str] | str]]:
    return HELP_SECTIONS_BY_LANGUAGE.get(language, HELP_SECTIONS_BY_LANGUAGE["en"])


def get_help_page_copy(language: str) -> dict[str, str]:
    return HELP_PAGE_COPY.get(language, HELP_PAGE_COPY["en"])
