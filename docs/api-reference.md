# Referência da API

[Voltar ao índice da documentação](README.md)

A API recebe medições de latência em milissegundos e permite consultar os
mesmos datasets por recursos, estatísticas e gráficos.

| Ambiente | URL base |
| --- | --- |
| Publicado | `https://api-performance-monitor-0vke.onrender.com` |
| Local com Docker | `http://localhost:8000` |

Em cada ambiente, use `/docs` para executar requisições pelo Swagger UI,
`/redoc` para ler a referência ou `/openapi.json` para obter a especificação.

## Primeiro dataset

No Swagger, abra **POST /datasets**, clique em **Try it out** e envie:

```json
{
  "latency_ms": [100, 120, 150]
}
```

A resposta `201 Created` inclui o `id` do dataset. Use esse ID nos campos
`dataset_id` das outras operações:

| Operação | O que experimentar |
| --- | --- |
| `GET /datasets/{dataset_id}` | Consultar as medições salvas. |
| `GET /datasets/{dataset_id}/statistics/mean` | Obter a média em milissegundos. |
| `GET /datasets/{dataset_id}/statistics/percentile?percent=95` | Consultar o percentil 95. |
| `GET /datasets/{dataset_id}/charts/histogram` | Gerar um histograma em PNG. |

Para adicionar uma medição, use **POST /datasets/{dataset_id}/measurements**
com `{"latency_ms": 130}`. As mesmas operações estão disponíveis no ambiente local.

As criações de datasets e medições devolvem `201 Created` e o cabeçalho
`Location` com a URL do recurso criado. A resposta da criação de um dataset
segue este formato; o ID é ilustrativo:

```json
{
  "id": 1,
  "latency_ms": [100.0, 120.0, 150.0]
}
```

A média desse exemplo, em `GET /datasets/{dataset_id}/statistics/mean`, é:

```json
{"value": 123.33333333333333}
```

As estatísticas escalares e contagens usam `value`; moda e outliers usam
`values`, com uma lista de números. Latências são expressas em milissegundos,
variâncias em ms² e proporções como frações de `0` a `1`.

## Datasets e medições

| Método | Caminho | Finalidade |
| --- | --- | --- |
| `POST` | `/datasets` | Criar um dataset. |
| `GET` | `/datasets` | Listar uma página de datasets. |
| `GET` | `/datasets/{dataset_id}` | Consultar um dataset. |
| `DELETE` | `/datasets/{dataset_id}` | Excluir um dataset e suas medições. |
| `POST` | `/datasets/{dataset_id}/measurements` | Adicionar uma medição. |
| `GET` | `/datasets/{dataset_id}/measurements` | Listar medições, opcionalmente filtradas por `latency_ms`. |
| `GET` | `/datasets/{dataset_id}/measurements/{measurement_id}` | Consultar uma medição. |
| `DELETE` | `/datasets/{dataset_id}/measurements/{measurement_id}` | Remover a medição identificada pelo ID. |

A listagem aceita `limit` (padrão `50`, de `1` a `100`) e `offset`
(padrão `0`, não negativo), em ordem crescente de ID. A resposta continua
sendo uma lista de datasets com suas medições. Por exemplo:
`/datasets?limit=50&offset=50`. Uma página sem resultados devolve `[]`.
As medições da página são carregadas em lote, sem uma consulta por dataset.

Liste as medições para descobrir seus IDs. O filtro `?latency_ms=100`
devolve somente as ocorrências desse valor: uma lista vazia indica ausência,
e seu tamanho informa a quantidade de ocorrências. Exclua cada medição pelo
seu ID. Ambas as exclusões devolvem `204 No Content`; a última medição de um
dataset não pode ser removida. O campo `position` preserva a ordem de inserção
e pode apresentar lacunas após exclusões.

## Estatísticas

| Método | Caminho | Finalidade |
| --- | --- | --- |
| `GET` | `/datasets/{dataset_id}/statistics/count` | Consultar a quantidade de medições. |
| `GET` | `/datasets/{dataset_id}/statistics/total` | Consultar a soma das latências. |
| `GET` | `/datasets/{dataset_id}/statistics/minimum` | Consultar a menor latência. |
| `GET` | `/datasets/{dataset_id}/statistics/maximum` | Consultar a maior latência. |
| `GET` | `/datasets/{dataset_id}/statistics/amplitude` | Consultar a diferença entre o maior e o menor valor. |
| `GET` | `/datasets/{dataset_id}/statistics/mean` | Consultar a média aritmética. |
| `GET` | `/datasets/{dataset_id}/statistics/median` | Consultar a mediana. |
| `GET` | `/datasets/{dataset_id}/statistics/mode` | Consultar as modas do dataset. |
| `GET` | `/datasets/{dataset_id}/statistics/variance` | Consultar a variância populacional ou amostral. |
| `GET` | `/datasets/{dataset_id}/statistics/standard-deviation` | Consultar o desvio padrão populacional ou amostral. |
| `GET` | `/datasets/{dataset_id}/statistics/first-quartile` | Consultar o primeiro quartil. |
| `GET` | `/datasets/{dataset_id}/statistics/second-quartile` | Consultar o segundo quartil. |
| `GET` | `/datasets/{dataset_id}/statistics/third-quartile` | Consultar o terceiro quartil. |
| `GET` | `/datasets/{dataset_id}/statistics/interquartile-range` | Consultar o intervalo interquartil. |
| `GET` | `/datasets/{dataset_id}/statistics/percentile` | Consultar um percentil. |
| `GET` | `/datasets/{dataset_id}/statistics/outliers` | Consultar possíveis valores atípicos. |
| `GET` | `/datasets/{dataset_id}/statistics/count-above` | Contar medições acima de um limite. |
| `GET` | `/datasets/{dataset_id}/statistics/proportion-above` | Consultar a proporção acima de um limite. |
| `GET` | `/datasets/{dataset_id}/statistics/count-at-or-below` | Contar medições menores ou iguais a um limite. |

As rotas de variância e desvio padrão aceitam o parâmetro de consulta
`sample`, com valor padrão `false`. A rota de percentil usa `percent=95` por
padrão, e as consultas por limite usam `threshold_ms=120`.

## Visualizações

Todas as rotas abaixo devolvem a imagem diretamente com `Content-Type: image/png`.

| Método | Caminho | Finalidade |
| --- | --- | --- |
| `GET` | `/datasets/{dataset_id}/charts/histogram` | Histograma com marcadores p50, p90, p95 e p99. |
| `GET` | `/datasets/{dataset_id}/charts/boxplot` | Mediana, quartis, dispersão e possíveis outliers. |
| `GET` | `/datasets/{dataset_id}/charts/timeline` | Latência pela ordem das medições, sem horários reais. |
| `GET` | `/datasets/{dataset_id}/charts/cumulative` | Percentual acumulado por latência. |
| `GET` | `/datasets/{dataset_id}/charts/frequency` | Quantidade de ocorrências de cada latência exata. |

O histograma aceita `bins` de `1` a `200` e `show_percentiles`, com padrão
`true`. Quando `bins` é omitido, usa a raiz quadrada da quantidade de medições,
arredondada para cima e limitada a 200 faixas. Por exemplo:
`/datasets/1/charts/histogram?bins=6&show_percentiles=false`.
Um dataset inexistente devolve `404`; parâmetros inválidos devolvem `422`,
ambos no contrato JSON de erros. As imagens são geradas em memória, sem
salvar arquivos no servidor.

Os gráficos aceitam até **10.000 medições por dataset**; o gráfico de
frequência aceita até **200 latências distintas**. Acima desses limites,
a API devolve `422`, sem truncar os dados. Para muitas latências distintas,
use o histograma. Esses limites são das visualizações, não da criação do dataset.

PNGs repetidos são reutilizados por um cache LRU de até **16 MiB e 64 entradas
por processo**, identificado pelo tipo do gráfico, opções e conteúdo atual das
medições. Adicionar ou remover medições muda a chave; excluir o dataset continua
retornando `404`. Reiniciar o processo descarta o cache. Acertos no cache não
aguardam a renderização de outros gráficos; renderizações novas continuam
protegidas pelo lock exigido pelo Matplotlib.

## Contrato de erros

Os erros conhecidos da API usam o mesmo formato de resposta:

```json
{
  "detail": "Descrição do erro."
}
```

- `404 Not Found`: o dataset ou a medição solicitada não existe;
- `409 Conflict`: a operação deixaria o dataset sem medições;
- `422 Unprocessable Content`: os dados de entrada ou uma regra de negócio são
  inválidos.

Os IDs de datasets e medições devem ser inteiros de `1` a `2147483647`,
conforme as colunas PostgreSQL. Valores fora desse intervalo devolvem `422`
antes da consulta ao banco.

O schema dessa resposta também aparece no OpenAPI e pode ser consultado pelo
Swagger UI.
