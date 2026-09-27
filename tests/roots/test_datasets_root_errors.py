"""Testes de erro de integração para as rotas de datasets_root.py.

Usa os fixtures `client`, `existing_dataset` e `single_measurement_dataset`
(definidos em conftest.py) para exercitar o pipeline completo: requisição
HTTP -> domínio -> handler -> resposta.
"""

from fastapi import status
from fastapi.testclient import TestClient

from api_performance_monitor.models.datasets_models import LatencyDatasetModel


def test_create_dataset_with_empty_measurements_returns_422(
    client: TestClient,
) -> None:

    """POST /Datasets/datasets/create com latency_ms=[] deve retornar 422 (EmptyLatencyDatasetError)."""
    body = {"latency_ms": []}
    response = client.post("/Datasets/datasets/create", json=body)
    assert response.status_code == 422


def test_create_dataset_with_negative_latency_returns_422(
    client: TestClient,
) -> None:
    """POST /Datasets/datasets/create com uma latência negativa deve retornar 422 (InvalidLatencyError)."""
    body = {"latency_ms": [-100]}
    response = client.post("/Datasets/datasets/create", json=body)
    assert response.status_code == 422


def test_get_dataset_details_with_unknown_id_returns_404(client: TestClient) -> None:
    """GET /Datasets/datasets/details/{id} com id inexistente deve retornar 404."""
    response = client.get("/Datasets/datasets/details/163")
    assert response.status_code == 404


def test_delete_dataset_with_unknown_id_returns_404(client: TestClient) -> None:
    """DELETE /Datasets/datasets/delete/{id} com id inexistente deve retornar 404."""
    response = client.delete("/Datasets/datasets/delete/165")
    assert response.status_code == 404


def test_add_measurement_to_unknown_dataset_returns_404(client: TestClient) -> None:
    """POST /Datasets/measurements/add/{id} em dataset inexistente deve retornar 404."""
    body = {
	"latency_ms": 156.12
    }
    response = client.post("/Datasets/measurements/add/564", json=body)
    assert response.status_code == 404


def test_add_measurement_with_negative_latency_returns_422(
    client: TestClient,
    existing_dataset: LatencyDatasetModel,
) -> None:
    """POST /Datasets/measurements/add/{id} com latência negativa deve retornar 422, mesmo em dataset existente."""
    id = existing_dataset.id

    body = {
        "latency_ms": -153
        }

    response = client.post(f"/Datasets/measurements/add/{id}", json=body)

    assert response.status_code == 422


def test_remove_measurement_from_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """DELETE /Datasets/measurements/remove/{id} em dataset inexistente deve retornar 404."""
    body = {
            "latency_ms": 153
            }
    response = client.delete("/Datasets/measurements/remove/645", json=body)
    assert response.status_code == 404


def test_remove_measurement_not_found_returns_404(
    client: TestClient,
    existing_dataset: LatencyDatasetModel,
) -> None:
    """Remover um valor que não está entre as medições do dataset deve retornar 404 (LatencyNotFoundError)."""
    assert False, "TODO: implementar"


def test_remove_last_measurement_returns_409(
    client: TestClient,
    single_measurement_dataset: LatencyDatasetModel,
) -> None:
    """Remover a única medição restante deve retornar 409 (DatasetWouldBecomeEmptyError)."""
    assert False, "TODO: implementar"


def test_measurement_contains_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """GET /Datasets/measurements/contains/{id} em dataset inexistente deve retornar 404."""
    assert False, "TODO: implementar"


def test_measurement_occurrences_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """GET /Datasets/measurements/occurrences/{id} em dataset inexistente deve retornar 404."""
    assert False, "TODO: implementar"
