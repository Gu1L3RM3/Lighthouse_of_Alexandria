# Plano de Implementacao - Toggle de Idioma no Menu com Default em Ingles

## 1. Resumo Executivo

Este documento define a implementacao de uma feature de idioma com escopo controlado:

- adicionar um botao no `MainMenuScene` para alternar entre `English` e `pt-BR`;
- iniciar o jogo em **ingles na primeira execucao**;
- persistir a escolha do jogador nas proximas execucoes;
- aplicar o idioma atual aos textos do menu;
- aplicar o idioma atual aos dialogos vindos de mapas `.tmx`;
- aplicar o idioma atual ao carregamento das `letters`, que hoje sao imagens com texto embutido.

O foco desta implementacao e entregar o comportamento pedido sem abrir uma refatoracao total do sistema inteiro de internacionalizacao. Ao mesmo tempo, a arquitetura deve seguir principios de **SOLID**, para evitar que a feature vire um conjunto de `if idioma == ...` espalhados pelo projeto.

## 2. Objetivo da Feature

### Comportamento esperado

O jogador devera conseguir:

- abrir o jogo pela primeira vez e ver o menu em ingles;
- alternar o idioma no menu principal;
- fechar e abrir o jogo novamente mantendo a ultima escolha;
- ver dialogos de mapas no idioma selecionado, quando a versao inglesa estiver disponivel;
- abrir letters com a imagem correspondente ao idioma atual.

### Resultado tecnico esperado

O sistema devera:

- centralizar a decisao do idioma atual;
- persistir essa preferencia em arquivo dedicado;
- expor uma API simples para cenas, spawners e carregadores de assets;
- manter fallback seguro para os dados legados em portugues.

## 3. Escopo

### Em escopo

- persistencia da preferencia de idioma;
- servico central para idioma atual;
- botao de troca de idioma no `MainMenuScene`;
- atualizacao dos textos do menu com base no idioma;
- suporte a dialogos `.tmx` com propriedade localizada;
- suporte a letters com variantes por idioma;
- validacoes e testes por fase.

### Fora de escopo nesta entrega

- traducao completa de todos os textos hardcoded em Python fora do menu;
- sistema generico de catalogo de traducao para o jogo inteiro;
- suporte a tres ou mais idiomas;
- dublagem;
- traducao automatica;
- edicao automatica das imagens das letters.

## 4. Diagnostico do Estado Atual

### Menu principal

O `MainMenuScene` possui textos fixos e botoes definidos diretamente no codigo:

- [code/scenes/main_menu_scene.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/main_menu_scene.py:137)

Hoje nao existe abstracao para idioma nem preferencia persistida para o menu.

### Dialogos de mapas

Os dialogos das areas sao lidos da propriedade `dialogo` dos objetos do mapa e divididos por `;`:

- [code/core/map/spawners/spawn.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/core/map/spawners/spawn.py:104)

Isso significa que o conteudo esta embutido no `.tmx`, hoje em portugues.

### Letters

As letters sao imagens fixas carregadas diretamente pelas cenas, por exemplo:

- [code/scenes/home_scene.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/home_scene.py:160)
- [code/scenes/home_after_scene.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/home_after_scene.py:168)
- [code/scenes/fases/level_1.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/fases/level_1.py:146)
- [code/scenes/fases/level_2.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/fases/level_2.py:224)
- [code/scenes/fases/generic_levels.py](/c:/Users/cavaz/OneDrive/Documentos/Projetos/Projetos_Python/IC/Alexandria/code/scenes/fases/generic_levels.py:331)

Como o texto esta rasterizado nas imagens, a traducao nao pode ser feita apenas no codigo. E necessario carregar assets diferentes por idioma.

## 5. Arquitetura Orientada por SOLID

## 5.1 Single Responsibility Principle

Cada unidade nova deve ter uma responsabilidade clara:

- `LanguagePreferencesRepository`
  - salvar e carregar a preferencia de idioma;
- `LanguageService`
  - manter o idioma atual em memoria, alternar idioma e expor textos simples do menu;
- `TmxDialogueResolver`
  - escolher qual propriedade do `.tmx` deve ser usada para montar as falas;
- `LetterAssetResolver`
  - resolver o caminho da imagem correta da letter de acordo com o idioma;
- `MainMenuScene`
  - apenas exibir o botao e reagir a interacao do usuario.

Isso evita:

- persistencia dentro da cena;
- logica de `.tmx` dentro do menu;
- paths condicionais de assets espalhados nas fases.

## 5.2 Open/Closed Principle

O sistema deve ser extensivel sem reescrever o fluxo principal.

Exemplos:

- hoje o toggle sera `en <-> pt-BR`;
- amanha, se houver `es`, a regra de alternancia pode crescer sem mexer em todas as cenas;
- novos mapas poderao adicionar `dialogo_en` mantendo compatibilidade com `dialogo`;
- novas letters localizadas poderao seguir uma convencao de nome sem mudar as cenas consumidoras.

## 5.3 Liskov Substitution Principle

As classes consumidoras nao devem depender de detalhes da implementacao de persistencia.

Exemplo:

- hoje o idioma sera salvo em `preferences.json`;
- no futuro pode ser salvo em outro formato.

Para isso, o restante do sistema deve depender do comportamento:

- carregar idioma;
- salvar idioma;
- recuperar idioma atual.

Nao deve depender do arquivo, formato JSON ou caminho fisico.

## 5.4 Interface Segregation Principle

Cada consumidor deve enxergar so o que precisa.

Exemplos:

- o menu precisa de:
  - `get_current_language()`
  - `toggle_language()`
  - `get_menu_label(key)`
- o spawner de dialogo precisa de:
  - `resolve_dialogue_lines(properties)`
- as cenas com letters precisam de:
  - `resolve_letter_asset(letter_id)`

Isso evita criar um manager inflado com API excessiva e acoplada demais.

## 5.5 Dependency Inversion Principle

As camadas mais altas devem depender de abstracoes simples, nao de detalhes concretos.

Na pratica:

- `MainMenuScene` depende de um servico de idioma;
- `DialogueAreaSpawner` depende de um resolvedor de dialogo;
- as cenas que abrem letters dependem de um resolvedor de asset;
- nenhum desses componentes deve montar regra de idioma por conta propria.

## 6. Design Proposto

### 6.1 Persistencia de idioma

Criar um arquivo dedicado a preferencias, separado do save de progresso.

Formato sugerido:

```json
{
  "schema_version": 1,
  "language": "en"
}
```

Regras:

- se o arquivo nao existir, assumir `en`;
- se o arquivo existir, carregar a ultima escolha;
- se estiver invalido, fallback para `en`.

### 6.2 Servico de idioma

Criar um `LanguageService` global, com responsabilidade limitada ao escopo da feature.

API inicial sugerida:

```python
service.get_current_language()
service.set_language("en")
service.toggle_language()
service.get_menu_label("start")
service.get_language_toggle_label()
```

Nessa primeira entrega, ele nao precisa ser um sistema completo de localizacao do jogo inteiro. Ele pode conter:

- labels do menu;
- nomes de idioma exibidos ao usuario;
- acesso ao idioma atual.

### 6.3 Resolucao de dialogos em `.tmx`

Criar uma regra de compatibilidade incremental:

- se o idioma atual for ingles e o objeto tiver `dialogo_en`, usar esse valor;
- senao usar `dialogo`.

Isso permite:

- manter todos os mapas atuais funcionando;
- migrar o conteudo gradualmente;
- nao quebrar fluxo existente.

### 6.4 Resolucao de letters

Criar uma convencao de nome para assets localizados:

- `letter_1_en.png`
- `letter_1_pt.png`
- `letter_2_en.png`
- `letter_2_pt.png`
- etc.

Um `LetterAssetResolver` transformara um identificador logico como `letter_1` no caminho real do asset.

As cenas deixam de carregar:

- `letters/letter_1.png`

e passam a carregar algo resolvido dinamicamente:

- `letters/letter_1_en.png`
- `letters/letter_1_pt.png`

## 7. Componentes Novos e Responsabilidades

### 7.1 `LanguagePreferencesRepository`

Arquivo sugerido:

- `code/core/repositories/language_preferences_repository.py`

Responsabilidades:

- localizar o arquivo de preferencias;
- carregar idioma salvo;
- salvar idioma escolhido;
- tratar erro de arquivo ausente ou invalido.

Nao deve:

- conhecer labels de menu;
- resolver dialogos;
- resolver assets.

### 7.2 `LanguageService`

Arquivo sugerido:

- `code/core/managers/language_service.py`

Responsabilidades:

- manter idioma atual;
- alternar entre `en` e `pt-BR`;
- devolver labels do menu;
- persistir alteracao via repositorio;
- expor o idioma para outros resolvedores.

Nao deve:

- editar mapas;
- abrir imagens diretamente;
- desenhar elementos de UI.

### 7.3 `TmxDialogueResolver`

Arquivo sugerido:

- `code/core/localization/tmx_dialogue_resolver.py`

Responsabilidades:

- receber propriedades do objeto do `.tmx`;
- escolher o texto certo para o idioma atual;
- dividir as falas por `;`.

Nao deve:

- instanciar `DialogueArea`;
- salvar preferencias;
- conhecer widgets de UI.

### 7.4 `LetterAssetResolver`

Arquivo sugerido:

- `code/core/localization/letter_asset_resolver.py`

Responsabilidades:

- receber algo como `letter_1`;
- devolver o caminho correto da imagem de acordo com o idioma.

Nao deve:

- carregar a imagem;
- abrir widgets;
- tocar eventos do jogo.

## 8. Estrategia de Implementacao por Fases

## Fase 1 - Infraestrutura minima de idioma

Objetivo:

- criar persistencia de idioma;
- criar servico de idioma;
- garantir default em ingles na primeira execucao.

Entregas:

- `LanguagePreferencesRepository`;
- `LanguageService`;
- inicializacao segura com fallback em `en`;
- testes unitarios dessas regras.

Validacoes:

- sem arquivo de preferencias, idioma deve ser `en`;
- com arquivo salvo em `pt-BR`, idioma deve ser `pt-BR`;
- alternancia deve persistir corretamente.

## Fase 2 - Toggle no MainMenuScene

Objetivo:

- adicionar botao de idioma no menu;
- atualizar labels do menu imediatamente ao alternar.

Entregas:

- novo botao no `MainMenuScene`;
- labels de menu vindas do `LanguageService`;
- comportamento visual coerente apos troca.

Validacoes:

- botao aparece no menu;
- toggle muda os textos sem reiniciar o jogo;
- fechar e abrir o jogo mantem a ultima escolha.

## Fase 3 - Dialogos de mapas `.tmx`

Objetivo:

- adaptar `spawn.py` para usar dialogo localizado quando existir.

Entregas:

- `TmxDialogueResolver`;
- suporte a `dialogo_en`;
- fallback para `dialogo`.

Validacoes:

- mapa antigo sem `dialogo_en` continua funcionando;
- mapa com `dialogo_en` usa ingles quando o idioma atual e `en`.

## Fase 4 - Letters localizadas

Objetivo:

- carregar a imagem correta da letter conforme o idioma.

Entregas:

- `LetterAssetResolver`;
- alteracao das cenas que hoje carregam paths fixos;
- convencao de assets `*_en.png` e `*_pt.png`.

Validacoes:

- em ingles, abrir letter carrega `_en`;
- em portugues, abrir letter carrega `_pt`;
- se uma variante nao existir, deve haver fallback previsivel.

## Fase 5 - Conteudo localizado e QA final

Objetivo:

- preencher mapas e assets com conteudo real;
- validar o fluxo completo.

Entregas:

- inclusao de `dialogo_en` nos mapas prioritarios;
- inclusao das letters traduzidas;
- rodada final de testes e validacoes manuais.

Validacoes:

- primeira abertura do jogo em ingles;
- toggle funcional no menu;
- dialogos de `.tmx` localizados;
- letters corretas por idioma;
- comportamento legado preservado.

## 9. Arquivos Alvo por Fase

### Fase 1

- `code/core/settings.py`
- `code/core/repositories/language_preferences_repository.py`
- `code/core/managers/language_service.py`
- possivelmente `code/game.py` para bootstrap
- `code/tests/...` para novos testes

### Fase 2

- `code/scenes/main_menu_scene.py`

### Fase 3

- `code/core/map/spawners/spawn.py`
- `code/core/localization/tmx_dialogue_resolver.py`
- mapas `.tmx` prioritarios

### Fase 4

- `code/core/localization/letter_asset_resolver.py`
- `code/scenes/home_scene.py`
- `code/scenes/home_after_scene.py`
- `code/scenes/fases/level_1.py`
- `code/scenes/fases/level_2.py`
- `code/scenes/fases/generic_levels.py`
- `assets/images/letters/...`

## 10. Testes e Validacoes

### Testes unitarios

Fase 1:

- carregar idioma padrao sem arquivo;
- salvar e recarregar idioma;
- alternar idioma.

Fase 3:

- resolver `dialogo_en` quando presente;
- fallback para `dialogo`.

Fase 4:

- resolver nome de asset correto por idioma;
- fallback previsivel se arquivo localizado nao existir.

### Validacoes manuais

- abrir o jogo pela primeira vez e verificar ingles;
- alternar para portugues no menu;
- fechar e abrir novamente;
- entrar em uma fase com dialogo de mapa;
- abrir uma letter;
- voltar ao menu e repetir o fluxo no outro idioma.

## 11. Riscos e Mitigacoes

### Risco 1 - Acoplamento excessivo

Se a logica de idioma for distribuida manualmente entre as cenas, a manutencao ficara cara.

Mitigacao:

- concentrar as decisoes em servicos e resolvedores dedicados.

### Risco 2 - Quebra de mapas antigos

Se a leitura de dialogo exigir obrigatoriamente `dialogo_en`, mapas antigos quebram.

Mitigacao:

- fallback sempre para `dialogo`.

### Risco 3 - Assets faltantes

Se uma letter em ingles nao existir, a cena pode falhar ao abrir a imagem.

Mitigacao:

- fallback para variante padrao;
- validacao manual e, se possivel, teste automatizado simples de resolucao de caminho.

### Risco 4 - Textos maiores no menu

Termos em ingles podem afetar layout dos botoes.

Mitigacao:

- revisar visualmente o menu apos a Fase 2;
- ajustar label do botao de idioma para manter largura segura.

## 12. Definicao de Pronto

A feature sera considerada pronta quando:

- o jogo abrir em ingles na primeira execucao;
- o idioma persistir entre sessoes;
- o `MainMenuScene` possuir toggle funcional entre `en` e `pt-BR`;
- os textos do menu atualizarem imediatamente;
- dialogos de `.tmx` respeitarem o idioma atual quando houver `dialogo_en`;
- letters carregarem a imagem correta do idioma;
- o fluxo legado continuar funcionando com fallback seguro.

## 13. Ordem Recomendada de Execucao

1. criar branch da feature;
2. implementar Fase 1;
3. rodar testes e validar Fase 1;
4. implementar Fase 2;
5. rodar testes e validar Fase 2;
6. implementar Fase 3;
7. rodar testes e validar Fase 3;
8. implementar Fase 4;
9. rodar testes e validar Fase 4;
10. preencher conteudo localizado e concluir QA final.

## 14. Recomendacao Final

Para este recorte, a melhor estrategia nao e construir um sistema completo de internacionalizacao do jogo inteiro de uma vez. O caminho mais seguro e implementar uma base pequena, orientada por SOLID, com responsabilidades bem separadas e compatibilidade com os dados legados.

Assim, entregamos o toggle do menu com default em ingles, damos suporte real aos dialogos de mapas e as letters, e deixamos o projeto preparado para futuras expansoes de idioma sem aumentar desnecessariamente a divida tecnica.
