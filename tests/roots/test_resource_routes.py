"""Contratos HTTP das coleções de datasets e medições."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api_performance_monitor.models.datasets_models import (
    LatencyDatasetModel,
    LatencyMeasurementModel,
)
from main import app


def test_dataset_creation_exposes_location_and_delete_uses_204(client: TestClient) -> None:
    created = client.post("/datasets", json={"latency_ms": [100, 200]})

    assert created.status_code == 201
    dataset_id = created.json()["id"]
    assert created.headers["location"].endswith(f"/datasets/{dataset_id}")
    assert client.get(created.headers["location"]).json() == created.json()

    deleted = client.delete(f"/datasets/{dataset_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/datasets/{dataset_id}").status_code == 404


def test_measurements_have_stable_ids_when_duplicates_are_removed(
    client: TestClient, db_session: Session
) -> None:
    dataset = client.post("/datasets", json={"latency_ms": [100, 100, 200]}).json()
    dataset_id = dataset["id"]
    collection = f"/datasets/{dataset_id}/measurements"
    measurements = client.get(collection).json()
    first_id, second_id, third_id = (item["id"] for item in measurements)
    assert len({first_id, second_id, third_id}) == 3
    matches = client.get(collection, params={"latency_ms": 100}).json()
    assert [item["latency_ms"] for item in matches] == [100, 100]
    assert client.get(collection, params={"latency_ms": 999}).json() == []

    removed = client.delete(f"{collection}/{first_id}")

    assert removed.status_code == 204
    assert removed.content == b""
    assert client.delete(f"{collection}/{first_id}").status_code == 404
    assert [item["id"] for item in client.get(collection).json()] == [second_id, third_id]

    added = client.post(collection, json={"latency_ms": 300})

    assert added.status_code == 201
    assert added.headers["location"].endswith(f"{collection}/{added.json()['id']}")
    assert client.get(added.headers["location"]).json() == added.json()
    assert [item["id"] for item in client.get(collection).json()] == [
        second_id,
        third_id,
        added.json()["id"],
    ]
    updated_dataset = client.get(f"/datasets/{dataset_id}").json()
    assert updated_dataset["latency_ms"] == [100, 200, 300]
    assert db_session.get(LatencyMeasurementModel, second_id).latency_ms == 100


def test_measurement_id_cannot_be_used_under_another_dataset(
    client: TestClient, existing_dataset: LatencyDatasetModel
) -> None:
    other = client.post("/datasets", json={"latency_ms": [300, 400]}).json()
    foreign_id = existing_dataset.measurements[0].id
    path = f"/datasets/{other['id']}/measurements/{foreign_id}"

    assert client.get(path).status_code == 404
    assert client.delete(path).status_code == 404
    own_path = f"/datasets/{existing_dataset.id}/measurements/{foreign_id}"
    assert client.get(own_path).status_code == 200


def test_statistics_are_nested_under_their_dataset(
    client: TestClient, existing_dataset: LatencyDatasetModel
) -> None:
    response = client.get(f"/datasets/{existing_dataset.id}/statistics/mean")

    assert response.status_code == 200
    assert response.json() == {"value": 150.0}


def test_openapi_documents_resource_paths_and_error_responses() -> None:
    paths = app.openapi()["paths"]

    assert "/datasets" in paths
    assert "/datasets/{dataset_id}/measurements/{measurement_id}" in paths
    assert "/datasets/{dataset_id}/statistics/mean" in paths
    assert "/Datasets/datasets/create" not in paths
    assert "/statistics/mean/{dataset_id}" not in paths
    assert set(paths["/datasets"]["post"]["responses"]) == {"201", "422"}
    delete_responses = paths[
        "/datasets/{dataset_id}/measurements/{measurement_id}"
    ]["delete"]["responses"]
    assert set(delete_responses) == {
        "204", "404", "409", "422"
    }
