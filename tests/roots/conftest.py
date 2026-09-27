"""Fixtures dos testes de integração das rotas (camada de API).

Cria um banco SQLite em memória isolado por teste e injeta um TestClient
com o get_db real substituído por esse banco de teste. Ajuste para
Postgres transacional se preferir manter paridade total com produção.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api_performance_monitor.database import Base, get_db
from api_performance_monitor.models.datasets_models import (
    LatencyDatasetModel,
    LatencyMeasurementModel,
)


@pytest.fixture()
def db_session():
    """Fornece uma sessão SQLite isolada com todas as tabelas criadas."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """Fornece um cliente HTTP cuja dependência de banco usa a sessão de teste."""

    def override_get_db():
        """Substitui a sessão da aplicação pela sessão SQLite do teste."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def existing_dataset(db_session):
    """Dataset persistido com duas medições, para cenários que exigem estado prévio."""
    model = LatencyDatasetModel(
        measurements=[
            LatencyMeasurementModel(position=1, latency_ms=100.0),
            LatencyMeasurementModel(position=2, latency_ms=200.0),
        ]
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture()
def single_measurement_dataset(db_session):
    """Cria um dataset com uma medição para testar a remoção proibida."""
    model = LatencyDatasetModel(
        measurements=[LatencyMeasurementModel(position=1, latency_ms=100.0)]
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model
