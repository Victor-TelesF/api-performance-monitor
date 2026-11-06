FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    MPLBACKEND=Agg

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY main.py alembic.ini ./
COPY alembic ./alembic

RUN useradd --create-home app
USER app

EXPOSE 8000

# Só inicia o servidor depois que todas as migrações forem aplicadas.
CMD ["/bin/sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
