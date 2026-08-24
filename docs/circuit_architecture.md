# Arquitetura de circuitos em memoria

O editor usa um documento JSON v2 como unica fonte persistida. Resolver, validar, calcular
Thevenin/Norton e configurar bombas acontece em memoria; arquivos SPICE nao participam do
runtime.

## Fluxo principal

1. `CircuitJsonRepository` le JSON v1 ou v2, valida o conteudo e entrega um
   `CircuitDocument` imutavel. Escritas usam arquivo temporario e substituicao atomica.
2. `CircuitEntityMapper` e a fronteira entre o documento e as entidades visuais do ECS.
   Sprites, fontes, offsets e conexoes derivadas nunca sao persistidos.
3. `CircuitGraphBuilder` transforma terminais em nos eletricos. `CircuitTopologyIndex`
   mantem o indice espacial e revisoes independentes de topologia e valores.
4. `DcMnaSolver` monta e resolve diretamente a MNA numerica com NumPy.
5. `CircuitAnalysisService` calcula equivalentes de Thevenin e Norton modificando grafos
   imutaveis em memoria.
6. `CircuitFileService` e o limite de aplicacao injetado em validadores e bombas.
7. `SpiceNetlistExporter` existe apenas para exportacao manual e nao e chamado pelo jogo.

## Compatibilidade e falhas

O decoder v1 e os aliases historicos ficam isolados nos adaptadores de migracao. Um load
invalido produz uma excecao tipada e o editor so troca suas entidades depois que leitura,
migracao, validacao e mapping terminam com sucesso.

## Testes e desempenho

A fixture `code/tests/fixtures/circuit_characterization_v2.json` fixa topologias, polaridades,
resultados e analises dos circuitos versionados. Para repetir o benchmark aquecido contra o
baseline anterior a migracao:

```powershell
$env:PYTHONPATH='code'
.\.venv\Scripts\python.exe code/benchmarks/benchmark_circuits.py --output docs/circuit_benchmark.json
```

O comando falha se a mediana do solver novo ultrapassar 50% da antiga ou se o carregamento
v2 ultrapassar 80% do decoder v1 no mesmo ambiente.
