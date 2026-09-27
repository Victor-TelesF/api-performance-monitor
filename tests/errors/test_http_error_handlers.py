"""Testes de erro para os handlers HTTP (errors/http_error_handlers.py).

Cada handler é chamado diretamente (sem subir a aplicação), com uma
exceção construída à mão, verificando apenas status code e corpo da
resposta. `_request` não é usado pelos handlers, então pode ser None.
Os handlers são `async def` — use `asyncio.run(...)` para chamá-los.
"""

import asyncio
import json

from api_performance_monitor.domain.exceptions import (
    DatasetWouldBecomeEmptyError,
    EmptyLatencyDatasetError,
    InsufficientMeasurementsError,
    InvalidLatencyError,
    InvalidPercentileError,
    InvalidThresholdError,
    LatencyNotFoundError,
)
from api_performance_monitor.errors.errors import DatasetNotFoundError
from api_performance_monitor.errors.http_error_handlers import (
    handle_dataset_not_found,
    handle_domain_error,
)


def test_handle_dataset_not_found_returns_404_with_detail() -> None:
    """DatasetNotFoundError deve virar 404 com o detail igual à mensagem da exceção."""
    error = DatasetNotFoundError(dataset_id=42)

    response = asyncio.run(handle_dataset_not_found(None, error))

    assert response.status_code == 404
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_404_for_latency_not_found() -> None:
    """LatencyNotFoundError é o único DomainError que deve virar 404."""
    error = LatencyNotFoundError("Latência não encontrada.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 404
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_409_for_dataset_would_become_empty() -> None:
    """DatasetWouldBecomeEmptyError deve virar 409 (conflito), não 422."""
    error = DatasetWouldBecomeEmptyError("O dataset ficaria vazio.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 409
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_422_for_invalid_latency() -> None:
    """InvalidLatencyError cai no caso genérico e deve virar 422."""
    error = InvalidLatencyError("Latência inválida.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_422_for_invalid_percentile() -> None:
    """InvalidPercentileError também cai no caso genérico (422)."""
    error = InvalidPercentileError("Percentil inválido.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_422_for_invalid_threshold() -> None:
    """InvalidThresholdError também cai no caso genérico (422)."""
    error = InvalidThresholdError("Limite inválido.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_422_for_empty_latency_dataset() -> None:
    """EmptyLatencyDatasetError também cai no caso genérico (422)."""
    error = EmptyLatencyDatasetError("Dataset vazio.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": str(error)}


def test_handle_domain_error_returns_422_for_insufficient_measurements() -> None:
    """InsufficientMeasurementsError também cai no caso genérico (422)."""
    error = InsufficientMeasurementsError("Medições insuficientes.")

    response = asyncio.run(handle_domain_error(None, error))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": str(error)}
