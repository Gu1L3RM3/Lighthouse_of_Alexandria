# Alexandria

**Alexandria** é um jogo 2D em Python/Pygame que mistura exploração, narrativa e desafios de análise de circuitos elétricos.

Você joga como **Kevin**, atravessando fases com inimigos, portas e painéis elétricos, enquanto tenta impedir uma mudança catastrófica na linha do tempo de Alexandria.

## Enredo (sem grandes spoilers)

Kevin descobre que o Farol de Alexandria está no centro de uma decisão impossível: salvar a cidade pode custar sua própria história familiar. Ao longo das fases, os painéis elétricos deixam de ser apenas puzzles e viram parte direta do conflito narrativo.

Temas principais:
- ciência e engenharia como ferramenta de decisão;
- escolhas com consequências históricas;
- relação entre pai e filho em rota de colisão.

## Principais Mecânicas

- Exploração em mapa top-down.
- Interação com NPCs, portas e painéis.
- Editor de circuitos com componentes coletáveis:
  - resistor;
  - fonte de tensão;
  - fonte de corrente;
  - nós, fios e GND.
- Validação automática de circuito via solver simbólico/numérico.
- Progressão por fases com conteúdo didático de eletricidade.
- Sistema de bomba (fases específicas) calibrado por circuito.

## Conteúdo Educacional por Fase

As fases explicativas cobrem:
- Lei de Ohm e potência elétrica;
- associação de resistores;
- Leis de Kirchhoff (KCL/KVL);
- equivalentes de Thévenin e Norton;
- máxima transferência de potência.

## Controles

- `W A S D`: movimentação.
- `E`: interagir (painéis, portas, objetos).
- `B`: posicionar bomba (quando disponível).
- `L`: alternar luz da fase.

No editor de circuito:
- `N`: Node
- `W`: Wire
- `G`: GND
- `R`: rotacionar
- `S`: Select
- `Delete`: Delete
- `Esc`: cancelar ferramenta atual

## Requisitos

- Python `3.11+`
- Dependências em [`requirements.txt`](requirements.txt):
  - `pygame-ce==2.5.3`
  - `numpy==2.2.5`
  - `pandas==2.2.3`
  - `PyTMX==3.32`
  - `sympy==1.13.3`
  - `pathfinding==1.0.18`
- Dependências de build (opcional) em [`requirements-build.txt`](requirements-build.txt):
  - `pyinstaller==6.16.0`

## Como Executar (desenvolvimento)

1. Criar e ativar ambiente virtual.
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. (Opcional) Instalar dependências de build:

```bash
pip install -r requirements-build.txt
```

4. Rodar o jogo:

```bash
python main.py
```

## Build para Windows

Exemplo de build manual com PyInstaller:

```powershell
pyinstaller --noconfirm Alexandria.spec
```

Guia detalhado em [`BUILD_WINDOWS.md`](BUILD_WINDOWS.md).

## Salvamento e Dados de Runtime

- Em desenvolvimento, os dados ficam em `code/` (circuitos, netlists e save).
- No executável Windows, arquivos graváveis são copiados para:
  - `%LOCALAPPDATA%\Alexandria\code\circuitos`
  - `%LOCALAPPDATA%\Alexandria\code\ltspice`

## Estrutura do Projeto

- `main.py`: ponto de entrada.
- `code/game.py`: loop principal e registro das cenas.
- `code/scenes/`: cenas do jogo (menu, fases, editor, finais).
- `code/core/`: ECS, managers, sistemas, ferramentas de circuito.
- `code/circuitos/`: circuitos em JSON.
- `code/ltspice/`: netlists/arquivos auxiliares.
- `assets/`: imagens, fontes, mapas e áudio.

## Stack Técnica

- Python + `pygame-ce`
- ECS próprio (Entity/Component/System)
- Solver de circuitos com `sympy` + `numpy/pandas`
- Mapas via `PyTMX`
- Navegação em grid com A* (`pathfinding`)

## Status

Projeto jogável com campanha em múltiplas fases, editor de circuito integrado e fluxo de build para Windows.

---

Se você quiser, eu também posso preparar uma versão do README com **GIFs/screenshots**, seção de **roadmap** e seção de **contribuição** (`CONTRIBUTING.md`).
