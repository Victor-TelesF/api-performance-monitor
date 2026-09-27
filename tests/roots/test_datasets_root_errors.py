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
    """Retorna 422 ao criar um dataset sem nenhuma medição."""
    body = {"latency_ms": []}
    response = client.post("/Datasets/datasets/create", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {
        "detail": "O dataset precisa de pelo menos uma medição."
    }


def test_create_dataset_with_negative_latency_returns_422(
    client: TestClient,
) -> None:
    """Retorna 422 ao criar um dataset com uma latência negativa."""
    body = {"latency_ms": [-100]}
    response = client.post("/Datasets/datasets/create", json=body)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {
        "detail": "A latência deve ser um número real, finito e não negativo."
    }


def test_get_dataset_details_with_unknown_id_returns_404(client: TestClient) -> None:
    """Retorna 404 ao consultar os detalhes de um dataset inexistente."""
    response = client.get("/Datasets/datasets/details/163")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}


def test_delete_dataset_with_unknown_id_returns_404(client: TestClient) -> None:
    """Retorna 404 ao tentar excluir um dataset inexistente."""
    response = client.delete("/Datasets/datasets/delete/165")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}


def test_add_measurement_to_unknown_dataset_returns_404(client: TestClient) -> None:
    """Retorna 404 ao adicionar uma medição a um dataset inexistente."""
    body = {"latency_ms": 156.12}
    response = client.post("/Datasets/measurements/add/564", json=body)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}


def test_add_measurement_with_negative_latency_returns_422(
    client: TestClient,
    existing_dataset: LatencyDatasetModel,
) -> None:
    """Retorna 422 ao adicionar uma latência negativa a um dataset."""
    body = {"latency_ms": -153}
    response = client.post(
        f"/Datasets/measurements/add/{existing_dataset.id}",
        json=body,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {
        "detail": "A latência deve ser um número real, finito e não negativo."
    }


def test_remove_measurement_from_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """Retorna 404 ao remover uma medição de um dataset inexistente."""
    response = client.delete(
        "/Datasets/measurements/remove/645",
        params={"measurement": 153},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}


def test_remove_measurement_not_found_returns_404(
    client: TestClient,
    existing_dataset: LatencyDatasetModel,
) -> None:
    """Retorna 404 ao remover uma latência que não existe no dataset."""
    measurement = 999.0
    response = client.delete(
        f"/Datasets/measurements/remove/{existing_dataset.id}",
        params={"measurement": measurement},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"A latência {measurement} ms não foi encontrada."
    }


def test_remove_last_measurement_returns_409(
    client: TestClient,
    single_measurement_dataset: LatencyDatasetModel,
) -> None:
    """Retorna 409 quando a remoção deixaria o dataset vazio."""
    response = client.delete(
        f"/Datasets/measurements/remove/{single_measurement_dataset.id}",
        params={"measurement": 100.0},
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "A última medição não pode ser removida."}


def test_measurement_contains_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """Retorna 404 ao procurar uma medição em um dataset inexistente."""
    response = client.get(
        "/Datasets/measurements/contains/45",
        params={"measurement": 500},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}


def test_measurement_occurrences_unknown_dataset_returns_404(
    client: TestClient,
) -> None:
    """Retorna 404 ao contar ocorrências em um dataset inexistente."""
    response = client.get(
        "/Datasets/measurements/occurrences/5",
        params={"measurement": 100},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Dataset não encontrado."}
