# Plano de Build Web Only

## 1. Resumo

Objetivo: gerar uma build jogavel no navegador para `Lighthouse of Alexandria`, mantendo a campanha e o editor de circuitos no modelo `web-only`.

Resultado esperado:
- uma pasta/build web com `index.html`, assets e runtime carregavel em hosting estatico;
- fluxo de save, preferencia de idioma e circuitos usando storage do browser;
- validacao dos paineis funcionando sem dependencia de `.net` e `.asc` em disco;
- pipeline reproduzivel para build local e publicacao.

Assumicoes:
- a rota principal de entrega sera Python no browser via WASM, preservando `pygame-ce` e o codigo atual;
- a primeira aposta tecnica deve ser `pygbag`;
- se houver bloqueio forte de compatibilidade/performance com `numpy`, `pandas` ou `sympy`, o plano passa para contingencia controlada, sem reabrir desktop path.

## 2. Escopo

### Em escopo

- preparar entrypoint e runtime para build browser;
- empacotar assets, mapas, fontes, audio e dados de painel;
- remover ou isolar pontos restantes dependentes de filesystem local;
- validar campanha, editor e resolucao dos paineis na build web;
- criar roteiro de deploy para hosting estatico.

### Fora de escopo

- suporte a controle;
- build desktop paralela;
- reescrita total para outra engine;
- backend online, login ou cloud save.

### Dependencias

- `pygame-ce`
- `PyTMX`
- `numpy`
- `pandas`
- `sympy`
- ferramenta de build web escolhida para Python/WASM

### Perguntas em aberto

- `pandas` e `sympy` entram no browser com custo aceitavel?
- o audio atual funciona integralmente no target web ou precisa degradacao controlada?
- o tamanho final da build cabe na estrategia de publicacao desejada?

## 3. Estrategia de Implementacao

### Fase 1: Auditoria de compatibilidade web

- levantar imports e caminhos criticos de runtime no `main.py`, [code/game.py](/C:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/game.py:1) e solver de circuitos;
- classificar dependencias em:
  - compativel com browser;
  - compativel com ajuste;
  - risco alto para WASM;
- medir quais bibliotecas realmente entram no loop de gameplay e quais podem ser atrasadas, lazy-loaded ou simplificadas.

Entrega:
- matriz de compatibilidade por dependencia;
- decisao formal: seguir com `pygbag` sem desvio ou abrir mitigacao tecnica.

### Fase 2: Entry point de build web

- criar um entrypoint dedicado de build web, sem bifurcacao desktop;
- garantir bootstrap de canvas, display, eventos de foco e preload de assets;
- preparar manifesto de assets obrigatorios para campanha minima e campanha completa.

Entrega:
- comando local unico para gerar build;
- jogo iniciando no browser com menu principal.

### Fase 3: Empacotamento de assets e dados

- garantir que mapas `.tmx`, imagens, audio, fontes e JSON de circuitos sejam resolvidos por caminho compativel com bundle web;
- revisar carregamento de recursos que ainda assumem path absoluto ou path mutavel;
- garantir que circuitos base dos paineis entrem no pacote como leitura inicial e que mutacoes continuem indo para storage do browser.

Entrega:
- build sobe sem `FileNotFoundError`;
- campanha abre cenas e paineis sem fallback local.

### Fase 4: Solver e validadores no browser

- validar `numpy`, `pandas` e `sympy` dentro da build real;
- medir tempo de resolucao de paineis mais pesados;
- se necessario, reduzir dependencias do solver para caminho menor, desde que sem quebrar regras atuais.

Entrega:
- todos os paineis obrigatorios resolvidos no browser;
- tempo de resposta aceitavel no editor e nos validadores.

### Fase 5: UX operacional web

- ajustar loading inicial, mensagens de erro e estados de foco/perda de aba;
- revisar audio, fullscreen, resize e retorno ao jogo;
- revisar ajuda e textos finais para linguagem de navegador.

Entrega:
- experiencia web coerente sem referencias residuais a desktop.

### Fase 6: Pipeline de publicacao

- definir comando de build;
- definir pasta de saida versionada;
- criar instrucoes de deploy para hosting estatico;
- preparar checklist de smoke test antes de publicar.

Entrega:
- build pronta para `itch.io`, `Cloudflare Pages` ou `Vercel`.

## 4. Plano TDD

Ordem recomendada:

1. teste de bootstrap web:
- prova que o entrypoint web inicia o jogo e chega ao menu sem acessar filesystem mutavel;
- implementacao: adaptar bootstrap e manifesto de assets.

2. testes de carregamento de recursos:
- provam que mapas, JSONs de paineis e assets base sao encontrados dentro do bundle;
- implementacao: ajustar resolucao de paths e loaders.

3. testes de integracao de solver no browser:
- provam que circuitos editados e paineis de campanha continuam resolvendo com storage do browser;
- implementacao: tratar gargalos restantes de IO e dependencia cientifica.

4. testes de smoke por fase:
- provam abertura de fase, abertura de painel, resolucao e conclusao;
- implementacao: fechar lacunas de runtime e validacao.

5. teste de build:
- prova que o comando de empacotamento gera artefato web valido;
- implementacao: script de build e verificacao minima da saida.

## 5. SOLID e Racional de Design

### Single Responsibility

- bootstrap web deve apenas iniciar runtime e registrar assets;
- storage deve continuar separado da logica de puzzle;
- solver nao deve conhecer hosting, deploy ou browser APIs diretamente.

### Open/Closed

- pipeline de build deve aceitar novos assets e fases sem reescrever o bootstrap;
- manifesto de empacotamento deve ser extensivel por configuracao.

### Liskov Substitution

- contratos de storage e leitura de netlist devem manter o mesmo comportamento esperado pelos validadores e pelo editor.

### Interface Segregation

- separar interface de build, interface de storage e interface de solver;
- evitar manager unico acumulando responsabilidades de runtime web e puzzle.

### Dependency Inversion

- build script deve depender de contratos de empacotamento e nao de chamadas espalhadas a paths;
- sistemas de fase devem continuar dependendo de `SerializationManager` e `CircuitManager`, nao de arquivo local.

## 6. Mudancas de Dados e Contratos

- sem mudanca de contrato de gameplay para o jogador;
- build web introduz contrato operacional novo:
  - comando oficial de build;
  - pasta oficial de saida;
  - manifesto oficial de assets;
- se houver cache busting, versionar nomes de artefato ou manifesto.

## 7. Observabilidade e Operacao

- logar falhas de preload de asset;
- logar falhas de solver por painel;
- logar tempo de resolucao dos paineis mais pesados;
- manter smoke test manual por:
  - menu;
  - entrada em fase;
  - editor;
  - painel validado;
  - save e reload.

## 8. Riscos e Mitigacoes

- `numpy`/`pandas`/`sympy` podem pesar ou falhar no target WASM.
  - mitigacao: medir cedo em build real; reduzir dependencia do solver se necessario.

- assets podem explodir tamanho da build inicial.
  - mitigacao: inventario de assets e carregamento sob demanda quando possivel.

- audio web pode falhar por politica de autoplay.
  - mitigacao: iniciar audio apenas apos interacao do usuario.

- path legado pode continuar escondido em fases especificas.
  - mitigacao: smoke tests por fase e grep orientado a `open`, `Path`, `exists`, `json.dump`, `json.load`.

- build aparentemente sobe, mas paineis falham so no browser real.
  - mitigacao: validar campanha dentro da build web, nao apenas em desktop.

## 9. Definition of Done

- comando de build web documentado e reproduzivel;
- build abre no navegador e chega ao menu;
- campanha principal e editor de circuitos executam na build web;
- paineis obrigatorios validam sem filesystem local;
- save e preferencias persistem no browser;
- testes relevantes de runtime, storage e gameplay estao passando;
- documentacao de deploy pronta.

## Ordem Recomendada

1. auditar compatibilidade das dependencias no target web;
2. criar entrypoint e script de build;
3. fechar empacotamento de assets e dados;
4. validar solver/paineis na build real;
5. rodar smoke tests por fase;
6. publicar primeiro em hosting estatico tecnico;
7. publicar depois em pagina de jogo.

## Destino Recomendado Quando Pronto

- `Cloudflare Pages` ou `Vercel` para hospedar a build estatica;
- `itch.io` para distribuicao publica do jogo HTML5.

Fluxo recomendado:
- gerar build estatico;
- validar em URL de preview;
- publicar release publica no `itch.io`.
