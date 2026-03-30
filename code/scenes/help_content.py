HELP_SECTIONS: list[dict[str, list[str] | str]] = [
    {
        "title": "Controles Básicos",
        "lines": [
            "W A S D: movimentação do personagem.",
            "E: interagir com portas, painéis e objetos próximos.",
            "B: posicionar bomba (somente nas fases que utilizam bomba).",
            "L: alterna a luz da fase (acende/apaga).",
        ],
    },
    {
        "title": "Objetivo do Jogo",
        "lines": [
            "Explore o mapa, leia os diálogos e resolva os desafios elétricos.",
            "Cada painel exige um circuito correto para liberar portas, luzes ou progresso.",
            "Use os itens coletados no mapa para montar o circuito correto no editor.",
        ],
    },
    {
        "title": "Como Abrir o Editor de Circuito",
        "lines": [
            "Aproxime-se de um painel de controle e pressione E.",
            "No desafio da bomba, use o botão NÚCLEO na interface da fase.",
            "Ao abrir o editor, monte o circuito e clique em Solve para validar.",
        ],
    },
    {
        "title": "Editor: Barra Superior (Botões)",
        "lines": [
            "Node: adiciona um nó de conexão.",
            "V Source: adiciona fonte de tensão (abre lista de valores disponíveis).",
            "Resistor: adiciona resistor (abre lista de valores disponíveis).",
            "I Source: adiciona fonte de corrente (abre lista de valores disponíveis).",
            "GND: adiciona o terra (referência obrigatória em vários circuitos).",
            "Wire: adiciona fio para conectar os componentes.",
            "X: salva e fecha o editor.",
        ],
    },
    {
        "title": "Editor: Barra Lateral (Botões)",
        "lines": [
            "R: ferramenta de rotação do componente selecionado.",
            "D: ferramenta de exclusão.",
            "S: ferramenta de seleção.",
            "Solve: salva o circuito atual, gera a netlist e resolve o circuito.",
            "Load: carrega o circuito salvo no arquivo atual.",
            "Clear: limpa os componentes editáveis.",
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
            "Também funcionam os atalhos: seta para cima/baixo.",
            "PageUp e PageDown rolam mais rápido.",
            "Home vai para o topo da lista e End vai para o final.",
        ],
    },
    {
        "title": "Fluxo Recomendado no Editor",
        "lines": [
            "1) Coloque o GND e os nós principais.",
            "2) Adicione fontes e resistores com valores corretos.",
            "3) Conecte tudo com Wire.",
            "4) Ajuste orientações com R e remova erros com D.",
            "5) Clique em Solve para validar os resultados.",
            "6) Saia pelo X quando terminar.",
        ],
    },
]