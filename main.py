"""Ponto de entrada da aplicação FastAPI.

As tabelas são criadas pelas migrações do Alembic antes de iniciar a API.
``app`` é o objeto FastAPI usado para receber requisições.
"""

from fastapi import FastAPI
from api_performance_monitor.errors.http_error_handlers import register_exception_handlers

from api_performance_monitor.roots import datasets_root

app = FastAPI(title="API PERFORMANCE MONITOR")

register_exception_handlers(app)
app.include_router(datasets_root.router)
