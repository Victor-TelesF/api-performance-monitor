"""Conexão com PostgreSQL e sessões usadas pela aplicação FastAPI.

``DATABASE_URL`` é montada pelo Settings a partir das variáveis ``POSTGRES_*``.
``sessionmaker`` cria sessões vinculadas ao engine do SQLAlchemy.
``SessionDep`` informa ao FastAPI que deve obter uma ``Session`` chamando
``get_db``; o contexto de dependência fecha a sessão após o uso.
"""


from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

from fastapi import Depends

from typing import Annotated
from .config import settings

DATABASE_URL = settings.database_url

db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False , autoflush=False,bind=db_engine)

class Base(DeclarativeBase):
    """Classe base de mapeamento do SQLAlchemy; guarda os metadados das tabelas."""
    pass

def get_db():
    """Fornece uma ``Session`` do SQLAlchemy e a fecha ao fim da dependência.

    O ``yield`` entrega a sessão ao código que a solicitou. Quando esse uso
    termina, o bloco ``finally`` executa ``db.close()`` mesmo se houve erro.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]
