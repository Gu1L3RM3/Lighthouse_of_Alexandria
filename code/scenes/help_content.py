HELP_SECTIONS: list[dict[str, list[str] | str]] = [
    {
        "title": "Controles Basicos",
        "lines": [
            "W A S D: movimentacao do personagem.",
            "E: interagir com portas, paineis e objetos proximos.",
            "B: posicionar bomba (somente nas fases que usam bomba).",
            "L: alterna a luz da fase (acende/apaga).",
            "Q: sair do jogo.",
        ],
    },
    {
        "title": "Objetivo do Jogo",
        "lines": [
            "Explore o mapa, leia os dialogos e resolva os desafios eletricos.",
            "Cada painel exige um circuito correto para liberar portas, luzes ou progresso.",
            "Use os itens coletados no mapa para montar o circuito certo no editor.",
        ],
    },
    {
        "title": "Como Abrir o Editor de Circuito",
        "lines": [
            "Chegue perto de um painel de controle e pressione E.",
            "No desafio da bomba, use o botao NUCLEO na interface da fase.",
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
            "Solve: salva o circuito atual, gera netlist e resolve o circuito.",
            "Load: carrega o circuito salvo no arquivo atual.",
            "Clear: limpa os componentes editaveis.",
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
