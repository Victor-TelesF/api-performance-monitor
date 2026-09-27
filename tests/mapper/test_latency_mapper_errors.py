"""Testes de erro para as conversões de mapper/latency_mapper.py.

Cobre apenas o caminho de erro quando o model vindo do banco é None
(dataset inexistente). Não depende de banco de dados real.
"""

import pytest

from api_performance_monitor.domain.latency import LatencyDataset
from api_performance_monitor.errors.errors import DatasetNotFoundError
from api_performance_monitor.mapper.latency_mapper import (
    model_to_domain,
    model_to_schema,
    update_model_from_domain,
)


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
