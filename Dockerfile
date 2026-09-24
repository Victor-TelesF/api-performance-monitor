FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

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

COPY main.py alembic.ini ./
COPY alembic ./alembic

RUN useradd --create-home app
USER app

EXPOSE 8000

CMD ["uv", "run", "--locked", "--no-sync", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
