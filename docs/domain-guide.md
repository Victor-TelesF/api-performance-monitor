# Guia do domínio e das visualizações

[Voltar ao índice da documentação](README.md)

Este guia reúne exemplos para estudar e testar diretamente as regras de
latência, sem iniciar a API ou o PostgreSQL.

## Preparar o ambiente

Na raiz do projeto, instale as dependências e abra o interpretador Python
gerenciado pelo `uv`:

```bash
uv sync --locked
uv run --locked python
```

Os blocos podem ser colados no interpretador na ordem apresentada. Outra opção
é reuni-los em um arquivo local e executá-lo com `uv run --locked python`.

## Criar um dataset e consultar estatísticas

```python
from api_performance_monitor.domain import LatencyDataset

dataset = LatencyDataset([100, 100, 110, 120, 130, 450])

print(dataset.count())           # 6 medições
print(dataset.measurements)      # (100.0, 100.0, 110.0, 120.0, 130.0, 450.0)
print(dataset.total())           # 1010.0 ms
print(dataset.minimum())         # 100.0 ms
print(dataset.maximum())         # 450.0 ms
print(dataset.amplitude())       # 350.0 ms: máximo - mínimo
print(f"{dataset.mean():.2f}")    # 168.33 ms
print(dataset.median())          # 115.0 ms
print(dataset.mode())            # (100.0,)
```

O construtor aceita uma coleção não vazia de números reais não negativos,
converte as medições para `float` e preserva sua ordem. A propriedade
`measurements` devolve uma tupla imutável.

## Quartis, percentis e dispersão

O bloco abaixo usa o `dataset` criado anteriormente:

```python
print(dataset.first_quartile())       # Q1 = 102.5 ms
print(dataset.second_quartile())      # Q2 = 115.0 ms
print(dataset.third_quartile())       # Q3 = 127.5 ms
print(dataset.interquartile_range())  # 25.0 ms

print(dataset.percentile(95))  # 370.0 ms
print(dataset.p50())           # 115.0 ms
print(dataset.p90())           # 290.0 ms
print(dataset.p95())           # 370.0 ms
print(dataset.p99())           # aproximadamente 434.0 ms

print(f"{dataset.variance():.2f}")                   # 15980.56 ms²
print(f"{dataset.standard_deviation():.2f}")         # 126.41 ms
print(f"{dataset.variance(sample=True):.2f}")        # 19176.67 ms²
print(f"{dataset.standard_deviation(sample=True):.2f}")  # 138.48 ms
print(dataset.outliers())                             # (450.0,)
```

Os percentis usam interpolação linear do NumPy. Por isso, um percentil pode
resultar em um valor que não existe exatamente no dataset. A variância e o
desvio padrão são populacionais por padrão; `sample=True` seleciona a fórmula
amostral, que exige pelo menos duas medições.

`outliers()` aplica os limites `Q1 - 1,5 × IQR` e `Q3 + 1,5 × IQR`. Os valores
encontrados mantêm a ordem original.

## Comparar medições com um limite

```python
limit_ms = 120

print(dataset.count_above(limit_ms))        # 2: 130 e 450 ms
print(dataset.count_at_or_below(limit_ms))  # 4: até 120 ms, inclusive
print(f"{dataset.proportion_above(limit_ms):.1%}")  # 33.3%
```

`count_above()` usa comparação estrita (`>`). `proportion_above()` devolve uma
fração entre `0.0` e `1.0`; o formato percentual altera apenas sua apresentação.

## Adicionar, remover e procurar medições

```python
dataset.add(120)                       # acrescenta ao final
print(dataset.count_occurrences(120))  # 2
print(dataset.contains(450))           # True

dataset.remove(120)                    # remove a primeira ocorrência
print(dataset.count_occurrences(120))  # 1
print(dataset.count())                 # 6
```

`add()` e `remove()` modificam o próprio objeto e devolvem `None`. O dataset
nunca pode ficar vazio, portanto `remove()` rejeita a exclusão da última
medição. Valores adicionados, removidos ou procurados sempre são validados.

## Tratar entradas inválidas

Os erros de regra herdam de `DomainError`, permitindo tratar uma condição
específica ou todos os erros do domínio:

```python
from api_performance_monitor.domain import (
    DomainError,
    InsufficientMeasurementsError,
    InvalidLatencyError,
    LatencyDataset,
)

try:
    LatencyDataset([100, -5])
except InvalidLatencyError as error:
    print(error)

try:
    LatencyDataset([100]).variance(sample=True)
except InsufficientMeasurementsError as error:
    print(error)

try:
    LatencyDataset([])
except DomainError as error:
    print(error)
```

Também são inválidos booleanos, `NaN` e infinitos. Percentis devem estar entre
0 e 100, enquanto limites de comparação devem ser finitos e não negativos.

## Gerar gráficos PNG

As funções de visualização recebem um `LatencyDataset` e devolvem uma
`matplotlib.figure.Figure`. `figure_to_png()` converte a figura em um
`io.BytesIO` contendo um PNG.

```python
from pathlib import Path

from api_performance_monitor.domain import LatencyDataset
from api_performance_monitor.visualization import (
    create_cumulative_distribution,
    create_latency_boxplot,
    create_latency_frequency_chart,
    create_latency_histogram,
    create_latency_timeline,
    figure_to_png,
)

dataset = LatencyDataset([100, 100, 110, 120, 130, 450])

figures = {
    "histogram": create_latency_histogram(dataset, bins=6),
    "boxplot": create_latency_boxplot(dataset),
    "timeline": create_latency_timeline(dataset),
    "cumulative": create_cumulative_distribution(dataset),
    "frequency": create_latency_frequency_chart(dataset),
}

for name, figure in figures.items():
    with figure_to_png(figure) as png:
        Path(f"{name}.png").write_bytes(png.getvalue())
```

| Função | Visualização |
| --- | --- |
| `create_latency_histogram()` | Quantidade por faixa e marcadores de percentis. |
| `create_latency_boxplot()` | Mediana, quartis, dispersão e possíveis outliers. |
| `create_latency_timeline()` | Latência pela ordem de cada medição. |
| `create_cumulative_distribution()` | Percentual acumulado por valor de latência. |
| `create_latency_frequency_chart()` | Quantidade de ocorrências de cada valor exato. |

`bins=None` escolhe automaticamente a quantidade de faixas do histograma.
`show_percentiles=False` oculta as linhas de percentis. As figuras não são
registradas globalmente no `pyplot`, e `figure_to_png()` não fecha a figura
recebida.

## Responsabilidades dos módulos

| Módulo | Responsabilidade |
| --- | --- |
| `domain/latency.py` | Dataset e operações públicas. |
| `domain/validation.py` | Validação de latências, percentis e limites. |
| `domain/statistics.py` | Implementação dos cálculos estatísticos. |
| `domain/exceptions.py` | Exceções das regras do domínio. |
| `visualization/charts.py` | Construção das figuras. |
| `visualization/export.py` | Conversão de figuras para PNG em memória. |
