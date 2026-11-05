"""Testes de erro para as conversões de mapper/latency_mapper.py.

Cobre datasets inexistentes e regras inválidas antes da conversão para ORM.
Não depende de banco de dados real.
"""

import pytest

from api_performance_monitor.domain import (
    EmptyLatencyDatasetError,
    InvalidLatencyError,
    LatencyDataset,
)
from api_performance_monitor.errors.errors import DatasetNotFoundError
from api_performance_monitor.mapper.latency_mapper import (
    model_to_domain,
    model_to_schema,
    schema_to_model,
    update_model_from_domain,
)
from api_performance_monitor.schemas.latency_dataset_schema import CreateLatencyDatasetSchema


@pytest.mark.parametrize(
    "values, error_type, message",
    (
        ([], EmptyLatencyDatasetError, "O dataset precisa de pelo menos uma medição."),
        ([100, -1, 200], InvalidLatencyError,
         "A latência deve ser um número real, finito e não negativo."),
        ([100, float("inf")], InvalidLatencyError,
         "A latência deve ser um número real, finito e não negativo."),
    ),
)
def test_schema_to_model_validates_before_constructing_persistable_models(values, error_type, message):
    schema = CreateLatencyDatasetSchema(latency_ms=values)
    with pytest.raises(error_type) as caught:
        schema_to_model(schema)
    assert str(caught.value) == message


def test_model_to_domain_raises_not_found_when_model_is_none() -> None:
    """model_to_domain(None) deve lançar DatasetNotFoundError."""
    with pytest.raises(DatasetNotFoundError):
        model_to_domain(None)


def test_model_to_schema_raises_not_found_when_model_is_none() -> None:
    """model_to_schema(None) deve lançar DatasetNotFoundError."""
    with pytest.raises(DatasetNotFoundError):
        model_to_schema(None)


def test_update_model_from_domain_raises_not_found_when_model_is_none() -> None:
    """update_model_from_domain(None, dataset) deve lançar DatasetNotFoundError."""
    dataset = LatencyDataset([100])

    with pytest.raises(DatasetNotFoundError):
        update_model_from_domain(None, dataset)
