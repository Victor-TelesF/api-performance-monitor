"""Ponto de entrada da aplicação FastAPI.

As tabelas são criadas pelas migrações do Alembic antes de iniciar a API.
``app`` é o objeto FastAPI usado para receber requisições.
"""

from fastapi import FastAPI

from api_performance_monitor.errors.http_error_handlers import (
    register_exception_handlers,
)
from api_performance_monitor.roots import datasets_root, statistics_root

tags_metadata = [
    {
        "name": "Datasets",
        "description": "Criação, listagem, consulta e exclusão dos datasets de latência.",
    },
    {
        "name": "Medições",
        "description": "Adição, remoção e consulta das medições de um dataset.",
    },
    {
        "name": "Estatísticas",
        "description": (
            "Consultas de tendência central, dispersão, percentis, limites "
            "e possíveis valores atípicos."
        ),
    },
]

app = FastAPI(
    title="API PERFORMANCE MONITOR",
    version="0.1.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "docExpansion": "none",
        "filter": True,
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": -1,
    },
)

register_exception_handlers(app)
app.include_router(datasets_root.router)
app.include_router(statistics_root.router)
