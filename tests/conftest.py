"""Configuração de teste independente do .env e dos bancos do desenvolvedor."""

import os

# O engine de produção é criado ao importar a aplicação. As rotas substituem
# get_db por SQLite; um override esquecido deve falhar, nunca acessar dados reais.
os.environ.update(
    POSTGRES_USER="test_user",
    POSTGRES_PASSWORD="test_password",
    POSTGRES_DB="api_performance_monitor_tests",
    POSTGRES_HOST="127.0.0.1",
    POSTGRES_PORT="1",
)
