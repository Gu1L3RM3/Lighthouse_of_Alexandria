# Plano de Port para Web com Firebase Analytics

## Resumo

Objetivo: portar o Alexandria para web, publicar uma versão jogável no navegador e instrumentar Firebase Analytics na build web.

Impacto observado:
- o jogo passa a rodar em browser via WebAssembly;
- eventos de uso e progresso passam a ser enviados ao Firebase Analytics;
- parte da infraestrutura de runtime deixa de depender de filesystem local e APIs desktop.

Principais restrições e premissas:
- stack atual: `Python + pygame-ce + PyInstaller`, com loop síncrono e persistência em arquivo local;
- alvo web mais viável hoje: `pygbag`;
- Firebase Analytics será integrado na camada web/JavaScript, não no código Python puro;
- primeira entrega deve priorizar "rodar no navegador" antes de otimizar UX, save e telemetria fina.

## Escopo

### In scope

- prova de conceito web com `pygbag`;
- adaptação mínima do loop principal para browser;
- auditoria e correção de incompatibilidades óbvias de web;
- publicação estática;
- integração inicial com Firebase Analytics;
- eventos básicos de gameplay e navegação;
- plano de fallback para persistência no browser.

### Out of scope

- reescrever o jogo para JS/TS/Phaser/Unity;
- refatorar toda a arquitetura ECS;
- multiplayer, backend autoritativo ou leaderboard;
- Remote Config nesta primeira fase;
- otimização profunda de performance antes da build rodar.

### Dependências

- `pygbag` / runtime wasm para `pygame-ce`;
- Firebase projeto web com Analytics habilitado;
- hospedagem estática, idealmente Firebase Hosting;
- validação de compatibilidade de `numpy`, `pandas`, `sympy`, `PyTMX`, `pathfinding`.

### Open questions

- a versão web precisa manter exatamente o mesmo save da desktop?
- áudio é obrigatório já na primeira entrega?
- o editor de circuito precisa estar disponível no lançamento web ou pode ficar para fase 2?
- qual o alvo principal: demo pública, MVP para teste com usuários, ou versão "completa"?

## Estratégia

### 1. Fase 0: Auditoria técnica

Mapear pontos desktop-specific no código:
- fullscreen em `code/game.py`
- save em arquivo em `code/core/managers/save_game_manager.py`
- resolução de paths e diretórios em `code/core/settings.py`
- áudio/autoplay em `code/core/managers/audio_manager.py`

Levantar incompatibilidades prováveis:
- loop síncrono bloqueante;
- `pygame.FULLSCREEN`;
- acesso a filesystem persistente;
- bibliotecas científicas em wasm;
- assets pesados e tempo de carregamento.

### 2. Fase 1: Vertical slice web sem Analytics

Objetivo: abrir o jogo no navegador, entrar no menu, iniciar uma cena e renderizar gameplay.

Mudanças esperadas:
- tornar o loop principal compatível com `pygbag`, tipicamente com `asyncio` e yield por frame;
- introduzir uma detecção de plataforma: desktop vs `emscripten`;
- desabilitar fullscreen no web e usar `set_mode()` normal com dimensões fixas ou responsivas;
- manter save em memória temporária, se necessário, só para validar boot.

Critério:
- menu abre;
- input funciona;
- troca de cena funciona;
- uma fase carrega.

### 3. Fase 2: Compatibilidade funcional

Resolver subsistemas que quebrarem no browser:
- áudio com interação do usuário antes de tocar música;
- persistência usando `localStorage` ou IndexedDB via ponte JS;
- adaptação de paths e possíveis arquivos não empacotados corretamente;
- performance e tamanho do bundle.

Aqui vale introduzir uma abstração de storage:
- `SaveStorage` interface;
- implementação `FileSaveStorage` para desktop;
- implementação `WebSaveStorage` para browser.

Isso evita espalhar `if web` pelo código.

### 4. Fase 3: Integração Firebase Analytics

Integrar Firebase no HTML/JS host da build web.

Expor uma ponte JS <-> Python para o jogo disparar eventos sem conhecer Firebase diretamente.

Introduzir um `TelemetryService` no Python:
- `track_event(name, params)`
- `set_user_property(name, value)` opcional
- `set_current_screen(scene_name)` opcional

Implementações:
- `NoopTelemetryService` para desktop;
- `WebTelemetryService` que chama a ponte JS e, daí, `logEvent()` do Firebase.

Eventos iniciais recomendados:
- `game_loaded`
- `menu_opened`
- `new_journey_started`
- `scene_changed`
- `level_started`
- `level_completed`
- `player_died`
- `save_resumed`
- `language_selected`
- `circuit_editor_opened`
- `panel_solved`

Parâmetros úteis:
- `scene_name`
- `level_name`
- `death_cause`
- `language`
- `session_mode`
- `build_version`

### 5. Fase 4: Publicação

- gerar build estática web;
- subir no Firebase Hosting;
- validar carregamento, console, network e eventos Analytics em ambiente publicado;
- configurar uma página simples de landing/loading se o bundle ficar pesado.

## Plano TDD

### 1. Testes de comportamento primeiro

Criar testes para a decisão de plataforma:
- "quando plataforma é web, usa configuração de display web";
- "quando plataforma é desktop, preserva comportamento atual".

Isso valida a extração das decisões do `Game`.

### 2. Testes unitários para abstrações novas

`PlatformService` ou helper de ambiente:
- detecta `emscripten` corretamente.

`SaveStorage`:
- contrato de `load/save/clear`.

`TelemetryService`:
- eventos inválidos não quebram o jogo;
- implementação noop não gera efeito colateral;
- implementação web monta payload correto.

### 3. Testes de integração nos boundaries

`SaveGameManager` usando storage abstrato:
- salva e carrega payload válido;
- rejeita schema inválido.

`SceneManager` + telemetry:
- mudança de cena dispara evento apenas uma vez;
- autosave continua funcionando sem regressão.

### 4. Regressões importantes

- transições de cena;
- fluxo de morte e resume;
- editor de circuito;
- idioma e preferências;
- ausência de telemetry ou bridge JS não pode derrubar o jogo.

Se TDD completo ficar difícil no início do port web, o melhor fallback é:
- escrever primeiro testes unitários das novas abstrações;
- validar o runtime web com smoke tests manuais estruturados.

## SOLID e desenho

### Single Responsibility

- `Game` hoje centraliza inicialização, loop, display e runtime behavior. O port vai ficar mais seguro se decisões de plataforma saírem dele.
- `SaveGameManager` deve continuar cuidando de regras de save, não de detalhes de filesystem/browser API.
- `TelemetryService` deve isolar analytics da lógica de gameplay.

### Open/Closed

- desktop e web devem entrar como implementações novas, não como cascata de `if sys.platform == ...` espalhada.
- interfaces pequenas para storage e telemetry tornam fácil adicionar outro backend depois.

### Liskov Substitution

- `FileSaveStorage` e `WebSaveStorage` precisam respeitar o mesmo contrato: mesmas garantias de retorno, mesmas falhas toleradas.

### Interface Segregation

- não criar um "PlatformManager" gigante.
- separar em contratos pequenos:
  - display/runtime config;
  - save storage;
  - telemetry.

### Dependency Inversion

- managers centrais devem depender de abstrações, não de Firebase nem de APIs JS diretamente.

## Contratos e dados

Mudanças de contrato internas:
- introdução de interface de storage para save;
- introdução de interface de telemetry;
- possível metadado de `build_version` e `platform` nos eventos.

Mudanças de payload:
- eventos analytics precisam de nomes estáveis e parâmetros limitados.
- evitar mandar dados livres demais para não poluir o GA4.

Compatibilidade:
- save desktop atual pode continuar como está;
- save web pode usar o mesmo schema JSON de `SaveGameManager`, o que reduz risco.

## Observabilidade e operação

Métricas mínimas:
- carregamento inicial concluído;
- taxa de entrada no gameplay;
- abandono entre menu e primeira fase;
- conclusão por fase;
- mortes por fase;
- tempo até primeira interação significativa.

Logs úteis na versão web:
- falha ao carregar assets;
- falha ao inicializar áudio;
- falha ao salvar/carregar estado;
- falha ao despachar evento analytics.

Operação:
- usar Firebase Hosting para servir os assets estáticos;
- manter versão identificável no cliente, ex.: `ALEX_BUILD_VERSION`.

## Riscos e mitigação

### 1. `pygbag` não suportar alguma parte crítica do runtime

Mitigação:
- spike curto logo no começo, antes de qualquer refactor grande.

### 2. `numpy/pandas/sympy` inflarem ou quebrarem a build

Mitigação:
- medir isso na Fase 1;
- se necessário, isolar solver e considerar simplificar dependências web.

### 3. Save local baseado em arquivo não funcionar bem no browser

Mitigação:
- abstrair storage cedo e começar com save em memória/localStorage.

### 4. Áudio falhar por políticas de autoplay

Mitigação:
- iniciar áudio apenas após input explícito do jogador.

### 5. Analytics acoplado demais ao core

Mitigação:
- bridge por `TelemetryService` com noop em desktop.

### 6. Bundle muito pesado e UX ruim no carregamento

Mitigação:
- landing page com loading progress, compressão e revisão de assets.

## Definição de pronto

- jogo abre no navegador e entra em pelo menos uma fase jogável;
- troca de cena funciona;
- input principal funciona;
- versão web é publicada em ambiente acessível;
- Firebase Analytics recebe eventos básicos reais;
- desktop continua funcionando;
- abstrações de storage e telemetry têm testes;
- principais regressões de save/scene transition foram validadas.

## Ordem recomendada

1. Spike `pygbag` mínimo.
2. Refactor pequeno para separar decisões de plataforma.
3. Build web com menu + 1 fase.
4. Storage web.
5. Firebase Analytics.
6. Publicação no Firebase Hosting.
7. Otimização e expansão para campanha completa.

## Hotspots de complexidade

- loop principal em `code/game.py`
- persistência em `code/core/settings.py` e `code/core/managers/save_game_manager.py`
- solver/dependências numéricas
- áudio no browser
