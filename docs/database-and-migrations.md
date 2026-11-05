# Banco de dados e migrações

[Voltar ao índice da documentação](README.md)

Este guia registra o fluxo de desenvolvimento do PostgreSQL e do Alembic. Para
uma primeira execução rápida da API, consulte o [README principal](../README.md).

## Modelo persistido

A revisão inicial `0001_create_latency_tables` cria duas tabelas normalizadas:

```mermaid
erDiagram
    LATENCY_DATASETS ||--|{ LATENCY_MEASUREMENTS : contains
    LATENCY_DATASETS {
        integer id PK
    }
    LATENCY_MEASUREMENTS {
        integer id PK
        integer dataset_id FK
        integer position
        float latency_ms
    }
```

Cada medição pertence a um dataset e possui uma posição positiva. O banco
rejeita latências negativas e posições repetidas dentro do mesmo dataset. A
relação ORM usa exclusão em cascata para remover as medições junto do dataset.

## Variáveis de ambiente

Copie o arquivo de exemplo antes de iniciar os containers:

```bash
cp .env.example .env
```

A classe `Settings`, em `config.py`, lê as variáveis `POSTGRES_*` e monta a URL
do SQLAlchemy. Entre containers, a API acessa o banco em `db:5432`. No host,
use `127.0.0.1:55432`. A variável `POSTGRES_HOST_PORT` define a porta publicada
pelo Compose, com padrão `55432`; `POSTGRES_PORT=5432` mantém a conexão interna.

Para aplicar uma mudança em `POSTGRES_HOST_PORT` a um banco já iniciado, execute
`docker compose up -d --no-deps db`. O container é recriado com o mesmo volume
`postgres_data`, preservando os dados.

O `.env` é local, não entra no Git e não é copiado para a imagem Docker.

## Inicialização com Docker

```bash
docker compose build api
docker compose up -d db
docker compose up -d api
```

O Compose aguarda o healthcheck do PostgreSQL antes de iniciar a API. O comando
padrão da imagem executa `alembic upgrade head` antes do Uvicorn e só inicia o
servidor se as migrações forem aplicadas com sucesso. Em um banco já atualizado,
o Alembic não reaplica as revisões existentes. Iniciar o Uvicorn diretamente,
fora desse comando Docker, ainda exige executar as migrações separadamente.

## Inspecionar o estado das migrações

Dentro do container:

```bash
docker compose exec api uv run --locked --no-sync alembic current
docker compose exec api uv run --locked --no-sync alembic history
```

No ambiente local, com o PostgreSQL do Compose ativo:

```bash
uv sync --locked
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55432 uv run --locked alembic current
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55432 uv run --locked alembic history
```

Se personalizar `POSTGRES_HOST_PORT`, substitua `55432` nos comandos locais
pela porta escolhida.

## Criar uma futura migração

Depois de alterar os modelos SQLAlchemy:

```bash
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55432 uv run --locked alembic revision --autogenerate -m "descricao_da_alteracao"
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55432 uv run --locked alembic upgrade head
```

Revise o arquivo gerado antes de aplicar a migração. Depois de alterar o código
ou adicionar revisões, reconstrua a imagem da API:

```bash
docker compose up -d --build api
```

## Volume e ciclo de vida

```bash
docker compose logs -f api
docker compose down
```

`docker compose down` remove os containers, mas preserva o volume
`postgres_data`. As variáveis `POSTGRES_*` inicializam o PostgreSQL apenas
quando esse volume está vazio.

O arquivo SQLite legado não é importado nem alterado pelo fluxo atual. No WSL,
habilite a integração da distribuição no Docker Desktop; quando necessário,
use `docker.exe` no lugar de `docker`.

## Upgrade e downgrade da revisão inicial

`upgrade()` cria `latency_datasets`, `latency_measurements`, índices e
restrições. `downgrade()` remove as duas tabelas e seus dados. Um downgrade é
destrutivo e deve ser usado somente quando a perda desses dados for aceitável.
