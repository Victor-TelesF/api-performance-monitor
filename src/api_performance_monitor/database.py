"""Objetos de acesso ao SQLite usados pela aplicação FastAPI.

``create_engine`` configura a conexão com o arquivo indicado por
``DATABASE_URL``. ``sessionmaker`` cria sessões vinculadas a esse engine.
``SessionDep`` informa ao FastAPI que deve obter uma ``Session`` chamando
``get_db``; o contexto de dependência fecha a sessão após o uso.
"""

from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

from fastapi import Depends

from typing import Annotated

DATABASE_URL = "sqlite:///./api_performance.db"

db_engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=db_engine)

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
