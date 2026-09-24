# API Performance Monitor

Projeto para analisar medições de latência de requisições, em milissegundos.
A API usa FastAPI e PostgreSQL, com a estrutura do banco versionada pelo Alembic.
Os exemplos de domínio e visualização mais abaixo também funcionam diretamente
em Python, sem iniciar a API ou o banco.

## Executar a API com Docker

Pré-requisito: Docker com Compose instalado e o motor do Docker iniciado.
Na raiz do projeto, prepare as variáveis locais:

```bash
cp .env.example .env
```

Os valores do exemplo são para aprendizado local. O `.env` não entra no Git
nem na imagem Docker. A classe `Settings`, em `config.py`, lê as variáveis
`POSTGRES_*` e monta a URL usada pelo SQLAlchemy. No Compose, a API recebe
essas variáveis pelo ambiente, com host `db` e porta `5432`.

Construa a imagem, inicie o banco, aplique a primeira migração e inicie a API:

```bash
docker compose build api
docker compose up -d db
docker compose run --rm api uv run --locked --no-sync alembic upgrade head
docker compose up -d api
```

Acesse o Swagger em <http://localhost:8000/docs>. Para conferir a persistência,
use `POST /Datasets/datasets/create` com `{"latency_ms": [100, 120, 150]}` e
depois `GET /Datasets/datasets/list`.

O Compose espera o PostgreSQL ficar pronto antes de iniciar o serviço da API.
As migrações são aplicadas explicitamente pelo comando acima; iniciar a API
não cria nem altera tabelas.

```bash
docker compose logs -f api
docker compose exec api uv run --locked --no-sync alembic current
docker compose down
```

`down` remove os containers, mas preserva os dados no volume `postgres_data`.
Na próxima execução, `docker compose up -d` inicia os serviços novamente.
O PostgreSQL começa vazio: o arquivo SQLite antigo não é alterado nem importado.
As variáveis `POSTGRES_*` inicializam o banco apenas quando o volume está vazio.

No WSL, habilite a integração da distribuição no Docker Desktop. Se estiver
usando o cliente Windows pelo WSL, os comandos também podem usar `docker.exe`
no lugar de `docker`.

## Primeira versão do banco

A revisão `0001`, em `alembic/versions/0001_create_latency_tables.py`, cria
`latency_datasets` e `latency_measurements`, incluindo a chave estrangeira,
os índices e as restrições presentes nos modelos. `upgrade()` cria essa
estrutura; `downgrade()` remove as duas tabelas e seus dados.

O arquivo `alembic/env.py` carrega `Base.metadata` e usa a mesma conexão da API.
`alembic current` mostra a revisão aplicada; `alembic history` mostra o histórico
dos arquivos de migração. Foi criada apenas a versão inicial.

Para praticar futuras migrações, execute o Alembic no ambiente local, para que
os novos arquivos sejam salvos no projeto. Com o PostgreSQL do Compose ativo:

```bash
uv sync --locked
POSTGRES_HOST=localhost uv run --locked alembic current
```

O `Settings` carrega as credenciais do `.env`. O comando acima substitui apenas
o host para acessar a porta publicada pelo Docker: no host, o endereço é
`localhost`; entre containers, é `db`.

Depois de uma alteração futura nos modelos, você poderá gerar uma revisão com
`POSTGRES_HOST=localhost uv run --locked alembic revision --autogenerate -m "descricao_da_alteracao"`,
revisar o arquivo e aplicá-lo com
`POSTGRES_HOST=localhost uv run --locked alembic upgrade head`.
Reconstrua a imagem com `docker compose up -d --build api` após mudar o código
ou adicionar migrações, pois os arquivos são copiados para a imagem no build.

## Preparar e executar

Na raiz do projeto, instale as dependências definidas em `pyproject.toml` e
abra o interpretador Python gerenciado pelo `uv`:

```bash
uv sync
uv run python
```

Cole os blocos Python a seguir nesse interpretador, na ordem apresentada. Se
preferir, reúna os blocos na mesma ordem em um arquivo `exemplos.py` e execute
com `uv run python exemplos.py`.

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

O construtor aceita uma coleção não vazia de números reais não negativos. Ele
converte as medições para `float` e preserva a ordem de entrada.
`measurements` devolve uma **tupla imutável**, que não permite alterar a
coleção por acidente.

## Quartis, percentis e dispersão

Este bloco usa o `dataset` criado acima:

```python
print(dataset.first_quartile())       # Q1 = 102.5 ms
print(dataset.second_quartile())      # Q2 = 115.0 ms; igual à mediana
print(dataset.third_quartile())       # Q3 = 127.5 ms
print(dataset.interquartile_range())  # 25.0 ms; Q3 - Q1

print(dataset.percentile(95))  # 370.0 ms
print(dataset.p50())           # 115.0 ms
print(dataset.p90())           # 290.0 ms
print(dataset.p95())           # 370.0 ms
print(dataset.p99())           # aproximadamente 434.0 ms

print(f"{dataset.variance():.2f}")            # 15980.56 ms²
print(f"{dataset.standard_deviation():.2f}")  # 126.41 ms
print(f"{dataset.variance(sample=True):.2f}")  # 19176.67 ms²
print(f"{dataset.standard_deviation(sample=True):.2f}")  # 138.48 ms
print(dataset.outliers())                    # (450.0,)
```

Os percentis usam a interpolação linear do NumPy. Por isso, o p95 pode ser
`370.0` mesmo sem nenhuma medição exatamente igual a `370.0`. `variance()` e
`standard_deviation()` usam a fórmula **populacional**. Para a fórmula
**amostral**, passe `sample=True` a qualquer um dos dois métodos; essa opção
exige pelo menos duas medições. A variância é expressa em ms² e o desvio padrão
em ms.

`outliers()` usa o intervalo entre Q1 − 1,5 × IQR e Q3 + 1,5 × IQR. Devolve as
medições fora desse intervalo na ordem original ou `()` quando não houver
nenhuma. `mode()` também devolve `()` quando todas as latências distintas têm
a mesma frequência.

## Medições acima ou dentro de um limite

```python
limite_ms = 120

print(dataset.count_above(limite_ms))        # 2: 130 e 450 ms
print(dataset.count_at_or_below(limite_ms))  # 4: até 120 ms, inclusive
print(f"{dataset.proportion_above(limite_ms):.1%}")  # 33.3%
```

`count_above()` usa comparação **estrita** (`>`). `proportion_above()` devolve
um `float` entre `0.0` e `1.0`; o formato `:.1%` apenas apresenta essa fração
como porcentagem.

## Adicionar, remover e procurar medições

```python
dataset.add(120)                       # acrescenta ao final; devolve None
print(dataset.count_occurrences(120))  # 2
print(dataset.contains(450))          # True

dataset.remove(120)                    # remove a primeira ocorrência; devolve None
print(dataset.count_occurrences(120))  # 1
print(dataset.count())                 # 6
```

O dataset nunca pode ficar vazio: `remove()` rejeita a exclusão da última
medição. Cada valor adicionado ou usado em uma busca é validado.

## Tratar entradas inválidas

Os erros do domínio herdam de `DomainError`. Assim, você pode tratar um caso
específico ou todos os erros de regra em um mesmo bloco:

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
    print(error)  # A latência deve ser um número real, finito e não negativo.

try:
    LatencyDataset([100]).variance(sample=True)
except InsufficientMeasurementsError as error:
    print(error)  # A variância amostral exige pelo menos duas medições.

try:
    LatencyDataset([])
except DomainError as error:
    print(error)  # O dataset precisa de pelo menos uma medição.
```

Também são inválidos booleanos, `NaN` e infinitos. Um percentil deve estar
entre 0 e 100; um limite de comparação deve ser finito e não negativo.

## Gerar gráficos PNG

As funções de `visualization` recebem um `LatencyDataset` e devolvem uma
`matplotlib.figure.Figure`. Nenhuma delas abre uma janela. `figure_to_png()`
converte essa figura em um `io.BytesIO`, um arquivo PNG em memória. O exemplo
abaixo grava os bytes em arquivos para você poder visualizar os gráficos:

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
    "histograma": create_latency_histogram(dataset, bins=6),
    "boxplot": create_latency_boxplot(dataset),
    "linha": create_latency_timeline(dataset),
    "acumulada": create_cumulative_distribution(dataset),
    "frequencia": create_latency_frequency_chart(dataset),
}

for name, figure in figures.items():
    with figure_to_png(figure) as png:
        Path(f"{name}.png").write_bytes(png.getvalue())
```

Os cinco arquivos `.png` são criados no diretório em que o comando Python foi
executado. O bloco `with` fecha cada `BytesIO` depois de usar seus bytes.
`figure_to_png()` não fecha a figura recebida; as figuras deste projeto são
criadas diretamente, sem registro global no `pyplot`.

| Função | O que mostra |
| --- | --- |
| `create_latency_histogram(dataset, bins=6)` | Quantidade de medições por faixa de latência; marca p50, p90, p95 e p99. |
| `create_latency_boxplot(dataset)` | Mediana, quartis, dispersão e possíveis outliers. |
| `create_latency_timeline(dataset)` | Latência pela **ordem** das medições, de 1 em diante; não usa horários reais. |
| `create_cumulative_distribution(dataset)` | Porcentagem de medições menores ou iguais a cada latência. |
| `create_latency_frequency_chart(dataset)` | Quantas vezes cada valor exato aparece; é mais legível com poucos valores distintos. |

No histograma, `bins=None` usa uma quantidade automática de faixas. Passe
`show_percentiles=False` para ocultar as linhas de percentis.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `domain/latency.py` | Classe pública `LatencyDataset` e operações de consulta e alteração. |
| `domain/validation.py` | Validação de latências, percentis e limites. |
| `domain/statistics.py` | Cálculos usados pelo dataset. |
| `domain/exceptions.py` | Erros de regras do domínio. |
| `visualization/charts.py` | Construção dos cinco tipos de gráficos. |
| `visualization/export.py` | Conversão de uma figura para PNG em memória. |
