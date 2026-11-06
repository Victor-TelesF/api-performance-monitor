"""Paginação HTTP e limite de consultas da listagem de datasets."""

import pytest
from sqlalchemy import event

from api_performance_monitor.models.datasets_models import (
    LatencyDatasetModel,
    LatencyMeasurementModel,
)


@pytest.fixture()
def many_datasets(db_session):
    db_session.add_all([
        LatencyDatasetModel(measurements=[
            LatencyMeasurementModel(position=1, latency_ms=value),
            LatencyMeasurementModel(position=2, latency_ms=value + 1),
        ])
        for value in range(105)
    ])
    db_session.commit()


def test_dataset_pages_have_stable_order_and_keep_response_shape(client, many_datasets):
    first = client.get("/datasets").json()
    second = client.get("/datasets", params={"limit": 50, "offset": 50}).json()
    last = client.get("/datasets", params={"offset": 100}).json()

    assert len(first) == len(second) == 50
    assert len(last) == 5
    assert [item["id"] for item in first + second + last] == list(range(1, 106))
    assert first[0] == {"id": 1, "latency_ms": [0.0, 1.0]}
    assert client.get("/datasets", params={"offset": 105}).json() == []
    assert len(client.get("/datasets", params={"limit": 100}).json()) == 100


@pytest.mark.parametrize("limit", [10, 100])
def test_listing_uses_two_queries_independent_of_page_size(
    client, db_session, many_datasets, limit
):
    queries = []
    engine = db_session.get_bind()

    def record(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        response = client.get("/datasets", params={"limit": limit, "offset": 3})
    finally:
        event.remove(engine, "before_cursor_execute", record)

    assert response.status_code == 200
    assert len(response.json()) == limit
    assert response.json()[0] == {"id": 4, "latency_ms": [3.0, 4.0]}
    assert len(queries) == 2


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": -1}, {"limit": 101}, {"limit": "1.5"},
    {"offset": -1}, {"offset": "invalid"},
])
def test_invalid_pagination_returns_standard_422(client, params):
    response = client.get("/datasets", params=params)
    assert response.status_code == 422
    assert response.json() == {"detail": "Dados de entrada inválidos."}
