"""Ponto de entrada da aplicação FastAPI.

Ao importar o módulo, ``create_all`` solicita ao SQLAlchemy a criação das
tabelas que já estiverem registradas em ``Base.metadata``. ``app`` é o objeto
FastAPI usado para receber requisições quando a aplicação for executada.
"""

from fastapi import FastAPI
from src.api_performance_monitor.database import Base, db_engine
from src.api_performance_monitor.http_error_handlers import register_exception_handlers

from src.api_performance_monitor.roots import latency_root

Base.metadata.create_all(db_engine)

app = FastAPI(title="API PERFORMANCE MONITOR")

register_exception_handlers(app)
app.include_router(latency_root.router)
