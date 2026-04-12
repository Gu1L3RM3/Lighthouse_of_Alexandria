HELP_SECTIONS: list[dict[str, list[str] | str]] = [
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
]
