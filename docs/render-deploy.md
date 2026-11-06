# GitHub Actions e deploy no Render

## Fluxo completo

```text
Push/merge em main
  → GitHub Actions instala Python e dependências do uv.lock
  → Executa pytest
  → Constrói a imagem Docker de produção
  → Inicia PostgreSQL temporário e a imagem pelo CMD real
  → Confere migrações, criação de dataset e reinicialização
  → Confere que falha de migração impede o servidor de iniciar
  → CI aprovado: Render reconstrói a imagem do commit de main
  → Alembic atualiza o banco configurado no Render
  → Uvicorn inicia e o Render verifica /openapi.json
```

O arquivo [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) roda em push
para `main`, pull requests direcionados a `main` e execução manual pelo GitHub.
Pull requests executam a validação; o deploy de produção acompanha a branch
`main`. O script [`check_docker_deploy.py`](../scripts/check_docker_deploy.py)
usa apenas containers descartáveis, sem portas publicadas ou banco de produção.

O Render aguarda os checks do GitHub por sua integração com o repositório.
Esse fluxo não exige deploy hook, token do Render nem credenciais de produção
nos secrets do GitHub. A imagem construída no CI valida o Dockerfile; o Render
constrói sua própria imagem do código aprovado, sem usar um registry intermediário.

O `Dockerfile` usa uma etapa de build para instalar as dependências de
`uv.lock`. A imagem final contém a `.venv`, o ponto de entrada e as migrações,
sem `uv`, ferramentas de teste ou CLIs do FastAPI. O comando de inicialização
aplica as migrações do Alembic e então inicia `main:app`.
O `render.yaml` registra uma configuração para um serviço web Docker no plano
gratuito, usando um PostgreSQL existente. O arquivo não provisiona o banco.

## Configurar o serviço que já existe

Em **Settings**, confira:

| Campo | Valor |
| --- | --- |
| Language / Runtime | Docker |
| Branch | `main` |
| Auto-Deploy | `After CI Checks Pass` |
| Root Directory | Vazio, pois o projeto está na raiz |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context Directory | `.` |
| Health Check Path | `/openapi.json` |

Deixe **Docker Command** vazio para usar o `CMD` do Dockerfile atualizado.
Se esse campo já contém apenas um comando Uvicorn, remova-o: ele substitui o
`CMD` da imagem e impede a execução automática das migrações.

Se precisar definir **Docker Command** explicitamente, use:

```sh
/bin/sh -c '/app/.venv/bin/alembic upgrade head && exec /app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"'
```

Tanto esse comando quanto o `CMD` aplicam as migrações antes de iniciar
a API. Se o Alembic falhar, o servidor não inicia. Não execute as migrações
durante o build da imagem.

Em **Environment**, preencha os dados do PostgreSQL de produção:

| Variável | Conteúdo |
| --- | --- |
| `POSTGRES_HOST` | Hostname do banco; use o interno para Render Postgres na mesma região |
| `POSTGRES_PORT` | Porta do banco, normalmente `5432` |
| `POSTGRES_DB` | Nome do banco |
| `POSTGRES_USER` | Usuário do banco |
| `POSTGRES_PASSWORD` | Senha do banco |

A aplicação atual lê essas cinco variáveis; configurar somente `DATABASE_URL`
não é suficiente. Use os campos de conexão fornecidos pelo banco. Os valores
locais `db`, `localhost` e `127.0.0.1` não apontam para um banco separado no Render.
`POSTGRES_HOST_PORT` pertence ao Compose local e não é usado nesse deploy.

O Render fornece `PORT`. O Dockerfile a respeita e usa `8000` quando ela não
existe, preservando a porta do Compose local.

Mantenha o repositório conectado pelo provedor GitHub e a branch `main`.
Depois de fazer commit e push, acompanhe **GitHub → Actions → CI**. Com todos
os checks aprovados, o Render inicia o deploy automaticamente. Se um check
falhar, corrija a falha antes de publicar outra alteração.

## Usar o Blueprint

O `render.yaml` pode ser usado ao criar um Blueprint conectado ao repositório.
Ele registra `branch: main` e `autoDeployTrigger: checksPass` para esse fluxo.
As variáveis com `sync: false` são preenchidas no painel, sem salvar
credenciais no Git. Novas variáveis de um Blueprint já existente precisam ser
adicionadas manualmente ao serviço.

Um serviço criado manualmente não passa a usar o Blueprint apenas porque o
arquivo foi enviado ao GitHub. Para manter o deploy que você já criou, siga
a configuração manual acima. Criar outro Blueprint pode criar outro serviço.

## Migrações e verificação

A configuração gratuita executa as migrações a cada inicialização e considera
uma única instância da aplicação. Antes de escalar para várias instâncias,
separe as migrações em uma etapa única de deploy. Em serviços pagos, o Render
oferece **Pre-Deploy Command**: use `/app/.venv/bin/alembic upgrade head`
nessa etapa e defina **Docker Command** para iniciar somente o servidor:

```sh
/bin/sh -c 'exec /app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"'
```

Confira os logs do Alembic e do Uvicorn e abra `/docs` e `/openapi.json` na URL
pública. A verificação em `/openapi.json` confirma que o processo HTTP responde;
ela não consulta o banco. Para verificar persistência, crie um dataset pelo
Swagger com `{"latency_ms": [100, 120, 150]}` e consulte o ID retornado.
A rota `/` não está definida nesta versão e pode responder `404` normalmente.

O `.env` é ignorado pelo Git e pelo contexto Docker. Mantenha as credenciais
no painel e use `.env.example` apenas como referência local.

## Reproduzir a validação de deploy localmente

Com o Docker iniciado:

```bash
uv sync --locked --dev
uv run --locked --no-sync pytest -q
docker build --tag api-performance-monitor:ci .
uv run --locked --no-sync python scripts/check_docker_deploy.py
```

O script exige que a imagem já tenha sido construída e remove os containers
temporários ao terminar. As credenciais fictícias usadas no teste são internas
ao ambiente descartável.

Referências: [Docker no Render](https://render.com/docs/docker),
[Blueprints](https://render.com/docs/blueprint-spec),
[porta HTTP](https://render.com/docs/web-services#port-binding) e
[integração com CI](https://render.com/docs/deploys#integrating-with-ci).
