"""Executa migrações usando a mesma conexão e os modelos da aplicação."""

from logging.config import fileConfig

from alembic import context

from api_performance_monitor.database import Base, db_engine
from api_performance_monitor.models import datasets_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar os modelos acima registra suas tabelas em Base.metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera SQL sem abrir conexão com o banco (opção --sql)."""
    context.configure(
        url=db_engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrações no banco indicado por DATABASE_URL."""
    with db_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
