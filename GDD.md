# Documento de Game Design - Farol de Alexandria

## 1. Identificacao do Projeto

**Titulo:** Farol de Alexandria  
**Genero:** aventura 2D top-down com puzzles educacionais de circuitos eletricos  
**Plataforma atual:** Windows desktop  
**Tecnologia principal:** Python com `pygame-ce`  
**Natureza do projeto:** jogo digital com finalidade ludica e educacional

## 2. Apresentacao

**Farol de Alexandria** e um jogo digital 2D que combina exploracao, narrativa e resolucao de desafios de analise de circuitos eletricos. O jogador assume o papel de **Kevin**, personagem que atravessa uma sequencia de fases enquanto investiga eventos ligados ao Farol de Alexandria e ao risco de uma alteracao catasrofica na linha do tempo.

O projeto foi concebido para integrar conteudos de eletricidade e circuitos a uma experiencia jogavel completa, evitando que os desafios tecnicos aparecam apenas como exercicios desconectados da progressao narrativa. Dessa forma, a resolucao de paineis eletricos passa a ser a propria linguagem de avancar no mundo, compreender a historia e enfrentar os conflitos centrais da campanha.

## 3. Proposta do Jogo

A proposta central do jogo e oferecer uma experiencia em que o jogador:

- explore mapas em perspectiva top-down;
- interaja com personagens, objetos e mecanismos;
- colete componentes eletricos distribuidos nas fases;
- monte circuitos em um editor integrado;
- valide solucoes com base em principios reais de analise de circuitos;
- avance na narrativa a partir do sucesso tecnico e estrategico.

O diferencial do projeto esta na integracao entre **conteudo didatico** e **estrutura dramatica**. Em vez de separar "fase de historia" e "fase de exercicio", o jogo utiliza os conceitos eletricos como parte do conflito, da progressao e do desafio geral.

## 4. Justificativa

Jogos educacionais frequentemente enfrentam o desafio de equilibrar dois objetivos: manter o engajamento ludico e preservar a consistencia pedagogica. Em muitos casos, os conteudos escolares aparecem de forma superficial ou artificial, reduzindo seu impacto tanto como jogo quanto como instrumento de aprendizagem.

**Farol de Alexandria** busca enfrentar esse problema por meio de tres principios:

1. o conteudo eletrico deve ser funcional dentro do sistema de jogo;
2. a progressao de dificuldade deve acompanhar a progressao conceitual;
3. o contexto narrativo deve motivar a resolucao dos desafios.

Essa abordagem torna o projeto relevante em contexto academico, especialmente em areas ligadas a:

- jogos educacionais;
- metodologias ativas de ensino;
- ensino de circuitos eletricos;
- design de sistemas interativos com finalidade formativa.

## 5. Objetivos

### 5.1 Objetivo Geral

Desenvolver um jogo digital 2D que integre exploracao, narrativa e resolucao de circuitos eletricos, com foco na aplicacao de conceitos de eletricidade em uma experiencia ludica e progressiva.

### 5.2 Objetivos Especificos

- apresentar conceitos fundamentais de circuitos ao longo da campanha;
- utilizar um editor de circuitos como mecanica principal de progressao;
- estruturar fases que articulem risco, exploracao e raciocinio tecnico;
- construir uma narrativa que reforce a motivacao do jogador;
- implementar validacao automatica das solucoes montadas pelo jogador;
- oferecer suporte ingame por meio de ajuda, prompts e fases explicativas;
- manter uma progressao coerente entre conteudo pedagogico e desafio jogavel.

## 6. Publico-Alvo

O projeto se dirige principalmente a:

- estudantes iniciantes ou intermediarios de eletricidade e circuitos;
- docentes e pesquisadores interessados em jogos educacionais;
- jogadores que apreciam puzzles sistemicos e experiencias narrativas;
- contextos academicos de demonstracao, extensao ou apoio didatico.

## 7. High Concept

O jogador explora ambientes 2D, interage com NPCs e resolve paineis eletricos por meio da montagem de circuitos corretos. Cada fase apresenta desafios associados a um conceito especifico de circuitos, enquanto a narrativa conduz o personagem por um conflito envolvendo familia, historia e responsabilidade sobre o destino de Alexandria.

## 8. Pilares de Design

Os pilares de design do projeto sao os seguintes.

### 8.1 Circuitos Como Mecanica Nuclear

Os circuitos nao atuam como acessorio ou minijogo secundario. Eles constituem o principal mecanismo de progressao do jogador.

### 8.2 Progressao Pedagogica Estruturada

Os conceitos eletricos sao introduzidos de forma gradual, com fases explicativas seguidas por fases aplicadas.

### 8.3 Integracao entre Sistema e Narrativa

As acoes do jogador sobre os paineis, portas e mecanismos sao coerentes com o universo ficcional e com a progressao dramatica da campanha.

### 8.4 Pressao Ludica Sobre o Conhecimento

O jogador nao apenas "resolve exercicios". Ele resolve problemas sob condicoes de exploracao, ameaca, escassez de recursos e urgencia.

## 9. Visao Geral da Experiencia

O fluxo completo atualmente identificado no projeto e o seguinte:

1. menu principal;
2. cena introdutoria na casa;
3. fase 1;
4. fase 2;
5. fase explicativa 3;
6. fase 3;
7. fase explicativa 4;
8. fase 4;
9. fase explicativa 5;
10. fase 5;
11. fase explicativa 6;
12. fase 6;
13. fase explicativa 7;
14. fase 7;
15. fase final;
16. cena de reacendimento do farol;
17. cena final em casa;
18. agradecimentos e creditos.

Essa estrutura indica que o projeto ultrapassa o escopo de prototipo mecanico, apresentando uma campanha fechada com abertura, desenvolvimento, climax e encerramento.

## 10. Loop Principal de Gameplay

O loop principal das fases pode ser descrito da seguinte forma:

1. explorar o mapa;
2. interagir com NPCs, portas, cartas ou areas de dialogo;
3. localizar componentes eletricos necessarios;
4. aproximar-se de um painel;
5. abrir o editor de circuitos;
6. montar o circuito com os componentes disponiveis;
7. validar a solucao;
8. receber uma consequencia no ambiente;
9. sobreviver aos perigos da fase;
10. avancar para a proxima etapa.

Esse loop mistura observacao, planejamento, resolucao tecnica e execucao espacial.

## 11. Controles

### 11.1 Exploracao

- `W A S D`: movimentacao
- `E`: interacao
- `B`: posicionamento de bomba, quando habilitado
- `L`: alternancia de luz
- `Esc`: menu
- `F1`: ajuda

### 11.2 Editor de Circuitos

- `N`: node
- `W`: wire
- `G`: GND
- `R`: rotacao
- `S`: selecao
- `Delete`: remocao
- `Esc`: cancelamento da ferramenta atual

## 12. Sistemas Principais

### 12.1 Movimento e Exploracao

O jogo utiliza movimentacao em perspectiva top-down, com camera seguindo o personagem, colisao com o ambiente e interacoes contextuais por proximidade.

### 12.2 Dialogos e Progressao Narrativa

A progressao narrativa depende de dialogos acionados por NPCs, areas de interacao ou objetos. Esses dialogos podem:

- desbloquear novas etapas;
- ativar papeis/cartas;
- liberar chaves;
- alterar o estado de personagens;
- conduzir o jogador entre cenas.

### 12.3 Editor de Circuitos

O editor de circuitos e a interface central do projeto. Nele, o jogador pode montar circuitos com:

- resistores;
- fontes de tensao;
- fontes de corrente;
- fios;
- nos;
- GND.

O editor permite criar, ajustar, validar, limpar e carregar configuracoes relacionadas a cada painel.

### 12.4 Sistema de Validacao

O jogo conta com validadores especializados para diferentes tipos de desafio. A validacao considera o circuito construído pelo jogador e verifica sua conformidade com os criterios esperados pela fase.

Foram identificadas no codigo as seguintes categorias principais:

- validacao de grandezas eletricas em resistor;
- validacao de associacao de resistores;
- validacao baseada em pares ou relacoes entre resistores;
- validacao de equivalentes de Thevenin e Norton;
- validacao de maxima transferencia de potencia.

### 12.5 Coleta e Armazenamento de Componentes

Os componentes distribuidos no mapa sao coletados pelo jogador e enviados para um armazenamento logico que alimenta o editor. Essa mecanica conecta diretamente exploracao e resolucao de problemas.

### 12.6 Inimigos e Pressao de Mapa

As fases intermediarias e finais apresentam ameacas como:

- fantasmas;
- aranhas e armadilhas de teia;
- morte por contato;
- invisibilidade temporaria;
- eventos de respawn.

Esses elementos aumentam a tensao e impedem que o jogo se reduza a uma experiencia puramente contemplativa ou teorica.

### 12.7 Sistema de Bomba / Nucleo

Algumas fases contam com um sistema de bomba calibrado por circuito. O jogador pode acessar um editor proprio de "nucleo", ajustando o comportamento desse recurso e utilizando-o em situacoes especificas da fase.

### 12.8 Sistema de Luz

Determinadas fases utilizam luz permanente ou temporaria como camada funcional e atmosferica. O sistema contribui para ambientacao e para a percepcao do estado do mapa.

### 12.9 Vida, Morte e Reentrada

O jogo possui gerenciamento global de vidas e fluxo de morte. Em caso de falha, a cena pode ser reiniciada com regras proprias de preservacao ou limpeza de estado.

### 12.10 Salvamento

O sistema de save registra:

- cena atual;
- quantidade atual de vidas;
- quantidade maxima de vidas.

As cenas de menu, ajuda e finais nao compoem estado persistente de retomada.

## 13. Estrutura de Cenas

### 13.1 Menu Principal

O menu principal oferece:

- continuar jornada;
- iniciar nova jornada;
- creditos;
- sair.

Sua funcao e estabelecer tom, identidade visual e acesso rapido ao estado salvo ou a uma nova partida.

### 13.2 Casa Inicial

A casa inicial cumpre papel introdutorio. Trata-se de uma cena mais narrativa, focada em contextualizacao e disparo da aventura principal.

### 13.3 Fases 1 e 2

As fases 1 e 2 funcionam como onboarding do universo do jogo, apresentando:

- exploracao;
- interacao com portas;
- uso de chaves;
- leitura de objetos narrativos;
- estrutura basica de progressao.

### 13.4 Fases Explicativas

As fases `exp_fase_3` a `exp_fase_7` introduzem conteudo teorico por meio de dialogos e sequencias visuais. Sua funcao e preparar o jogador para os desafios aplicados subsequentes.

### 13.5 Fases de Aplicacao

As fases 3 a 7 compoem o nucleo do jogo, combinando:

- coleta de componentes;
- puzzles com painel;
- inimigos e risco espacial;
- aplicacao direta de conceitos eletricos.

### 13.6 Fase Final

A fase final introduz maior pressao sistemica, exigindo resolucao sucessiva de multiplos paineis ativos, com temporizacao e possibilidade de reinicio parcial do desafio.

### 13.7 Finais

O encerramento do jogo se distribui em:

- reacendimento do farol;
- retorno a casa;
- carta final;
- creditos e agradecimentos.

## 14. Progressao Pedagogica

O projeto apresenta uma progressao conceitual clara.

### 14.1 Fase 3

Conceitos centrais:

- Lei de Ohm;
- potencia eletrica;
- GND como referencia;
- leitura de tensao, corrente e potencia.

### 14.2 Fase 4

Conceitos centrais:

- associacao em serie;
- associacao em paralelo;
- reducao de circuitos mistos;
- divisor de tensao.

### 14.3 Fase 5

Conceitos centrais:

- Leis de Kirchhoff;
- metodo nodal;
- formulacao de equacoes de circuito.

### 14.4 Fase 6

Conceitos centrais:

- equivalente de Thevenin;
- equivalente de Norton;
- obtencao de `Vth`, `Rth`, `In` e `Rn`.

### 14.5 Fase 7

Conceito central:

- maxima transferencia de potencia.

### 14.6 Fase Final

Conceito central:

- aplicacao sob pressao da maxima transferencia de potencia e do gerenciamento eficiente de recursos e tempo.

## 15. Ficha Resumida de Fases

### 15.1 Casa Inicial

- funcao: introducao narrativa;
- foco: ambientacao e gatilho inicial;
- transicao: fase 1.

### 15.2 Fase 1

- funcao: introducao de interacao e progressao;
- foco: chave, porta, papel e dialogo;
- transicao: fase 2.

### 15.3 Fase 2

- funcao: consolidacao do fluxo inicial;
- foco: sequencia narrativa e preparacao didatica;
- transicao: fase explicativa 3.

### 15.4 Fase 3

- funcao: primeira fase fortemente tecnico-ludica;
- foco: grandezas eletricas;
- pressao adicional: inimigos e morte por toque.

### 15.5 Fase 4

- funcao: consolidacao de associacao de resistores;
- foco: equivalencia e arranjo de componentes;
- pressao adicional: ameaças e teias.

### 15.6 Fase 5

- funcao: aumento da carga analitica;
- foco: relacoes entre valores e leituras de circuito;
- pressao adicional: exploracao em ambiente hostil.

### 15.7 Fase 6

- funcao: introducao de Thevenin/Norton em contexto jogavel;
- foco: equivalentes e fontes;
- pressao adicional: combinacao de coleta, validacao e ameaca.

### 15.8 Fase 7

- funcao: climax narrativo intermediario;
- foco: maxima transferencia de potencia;
- diferencial: confronto com o pai e disparo do arco final.

### 15.9 Fase Final

- funcao: prova final de dominio mecanico e conceitual;
- foco: resolucao sequencial de paineis temporizados;
- diferencial: resets parciais, necessidade de rota eficiente e alta pressao de execucao.

## 16. Narrativa

### 16.1 Premissa

Kevin descobre que o Farol de Alexandria esta no centro de um evento capaz de alterar profundamente a historia. Seu pai pretende modificar uma condicao critica do farol para favorecer uma linha temporal em que a avo de Kevin sobreviveria, ainda que isso implique a destruicao de Alexandria.

### 16.2 Conflito Central

O conflito dramático do jogo se organiza entre tres eixos:

- salvar Alexandria;
- impedir o plano do pai;
- lidar com o fato de que a propria existencia de Kevin esta associada a uma linha temporal alternativa.

### 16.3 Tom Narrativo

O tom do jogo combina:

- aventura historico-ficcional;
- drama familiar;
- urgencia moral;
- racionalidade cientifica aplicada a escolhas irreversiveis.

## 17. Personagens Principais

### 17.1 Kevin

Protagonista jogavel. Representa a articulacao entre curiosidade tecnica, responsabilidade historica e conflito afetivo.

### 17.2 Pai de Kevin

Antagonista tragico. Sua motivacao nao se reduz a destrutividade, mas a uma tentativa de reescrever um resultado historico com impacto direto sobre sua propria familia.

### 17.3 Arquimedes

Figura de apoio tecnico e narrativo. Atua como guia, conselheiro e reforco da compreensao dos desafios enfrentados pelo jogador.

## 18. Interface e Apoio ao Jogador

O projeto apresenta elementos de HUD e apoio contextual, incluindo:

- indicador de vidas;
- prompts contextuais de interacao;
- acesso rapido a menu e ajuda;
- status de bomba;
- barra de stealth;
- indicador de sobrecarga de componentes.

Adicionalmente, existe uma cena de ajuda com instrucoes sobre controles, funcionamento do editor e fluxo recomendado para resolucao.

## 19. Regras de Falha

As principais condicoes de falha observadas no projeto sao:

- contato letal com inimigos;
- quedas ou eventos ambientais;
- falha em manter certos estados de painel na fase final;
- perda de controle espacial em fases com maior pressao.

As consequencias da falha podem envolver morte, reinicio de secao, limpeza de componentes ou necessidade de recomposicao de circuitos.

## 20. Audio e Atmosfera

O jogo utiliza musicas e efeitos sonoros para delimitar contextos de jogo, incluindo:

- trechos narrativos e domesticos;
- fases explicativas;
- fases gerais de exploracao;
- fase 7, com atmosfera propria;
- fase final e encerramentos.

Os efeitos sonoros reforcam interacoes, resolucao de paineis, coleta, explosoes, morte e o momento simbólico de reacendimento do farol.

## 21. Estado Atual do Projeto

Com base no codigo analisado, o projeto ja apresenta:

- campanha completa com encadeamento de cenas;
- menu principal funcional;
- sistema de ajuda;
- editor de circuitos integrado ao fluxo de jogo;
- validadores especializados por topico;
- fases explicativas com apoio visual;
- sistema de save;
- sistema de vidas;
- sistema de inimigos;
- sistema de bomba;
- cenas finais e creditos.

Portanto, o estado atual caracteriza um jogo jogavel com estrutura completa, ainda que sujeito a refinamentos de documentacao, balanceamento e apresentacao.

## 22. Potencial Academico do Projeto

Do ponto de vista academico, o projeto apresenta potencial de contribuicao em:

- investigacao sobre integracao entre ludicidade e ensino de circuitos;
- estudo de progressao pedagogica em jogos digitais;
- aplicacao de simulacao e validacao automatica em contexto educacional;
- experimentacao com narrativa como fator de motivacao para aprendizagem.

Tambem oferece um caso interessante de articulacao entre:

- design de jogo;
- programacao de sistemas interativos;
- conteudo tecnico-cientifico;
- interface educacional.

## 23. Limitacoes e Desafios

Alguns desafios de design e pesquisa devem ser considerados.

### 23.1 Sobrecarga Cognitiva

O jogo exige simultaneamente:

- leitura de dialogos;
- exploracao espacial;
- identificacao de perigo;
- raciocinio tecnico;
- operacao do editor.

Isso exige cuidado com onboarding e clareza de objetivos.

### 23.2 Balanceamento

E necessario equilibrar:

- dificuldade conceitual;
- dificuldade espacial;
- ritmo narrativo;
- tempo de tentativa e erro.

### 23.3 Clareza Didatica

Os objetivos de cada painel devem permanecer explicitamente compreensiveis para que o jogador identifique se o problema esta:

- na interpretacao conceitual;
- na montagem do circuito;
- na escolha dos valores;
- na estrategia de execucao da fase.

## 24. Recomendações para Evolucao do Documento

Esta versao do GDD funciona como base academica inicial. Recomenda-se, como trabalho futuro:

1. inserir imagens e capturas de tela por fase;
2. adicionar fluxogramas da campanha;
3. registrar criterios de validacao em apendice tecnico;
4. detalhar roteiro e dialogos principais;
5. documentar licencas e origem de assets;
6. incluir observacoes de testes com usuarios;
7. registrar dados de balanceamento por fase.

## 25. Consideracoes Finais

**Farol de Alexandria** configura-se como um jogo digital que articula exploracao, narrativa e analise de circuitos em uma campanha estruturada. Sua principal contribuicao de design esta em transformar conteudos tecnicos de eletricidade em instrumentos reais de progressao dramatica e sistemica, aproximando o aprendizado de uma experiencia jogavel significativa.

Sob perspectiva academica, o projeto demonstra potencial tanto como produto interativo quanto como objeto de estudo em jogos educacionais, design de sistemas e ensino mediado por tecnologia.
