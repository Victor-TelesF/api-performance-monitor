"""Entradas rejeitadas por HTTP devem preservar todas as linhas persistidas."""

import pytest

INVALID_LATENCY = "A latência deve ser um número real, finito e não negativo."
INVALID_REQUEST = "Dados de entrada inválidos."


@pytest.mark.parametrize(
    "value, detail",
    ((True, INVALID_REQUEST), (False, INVALID_REQUEST), (None, INVALID_REQUEST),
     ("invalid", INVALID_REQUEST), ({}, INVALID_REQUEST), ([], INVALID_REQUEST),
     (-1, INVALID_LATENCY), ("NaN", INVALID_LATENCY),
     ("Infinity", INVALID_LATENCY), ("-Infinity", INVALID_LATENCY),
     ("1e9999", INVALID_LATENCY)),
)
@pytest.mark.parametrize("operation", ("create", "add"))
def test_invalid_latency_does_not_persist_partial_data(
    assert_http_error, existing_dataset, operation, value, detail
):
    path = "/datasets" if operation == "create" else f"/datasets/{existing_dataset.id}/measurements"
    body = {"latency_ms": [100, value, 200] if operation == "create" else value}
    assert_http_error("POST", path, 422, detail, json=body)


@pytest.mark.parametrize("operation", ("create", "add"))
@pytest.mark.parametrize("body", ({}, {"latency": 100}, None, [], "invalid"))
def test_malformed_request_body_is_rejected(
    assert_http_error, existing_dataset, operation, body
):
    path = "/datasets" if operation == "create" else f"/datasets/{existing_dataset.id}/measurements"
    assert_http_error("POST", path, 422, INVALID_REQUEST, json=body)


def test_malformed_json_is_rejected(assert_http_error, existing_dataset):
    assert_http_error(
        "POST", "/datasets", 422, INVALID_REQUEST,
        content='{"latency_ms": [100,', headers={"content-type": "application/json"},
    )


@pytest.mark.parametrize("latency", ("-1", "nan", "inf", "-inf", "1e9999"))
def test_measurement_filter_rejects_invalid_numeric_latency(
    assert_http_error, existing_dataset, latency
):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/measurements", 422,
        INVALID_LATENCY, params={"latency_ms": latency},
    )


@pytest.mark.parametrize("latency", ("true", "invalid", ""))
def test_measurement_filter_rejects_nonnumeric_latency(
    assert_http_error, existing_dataset, latency
):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/measurements", 422,
        INVALID_REQUEST, params={"latency_ms": latency},
    )


@pytest.mark.parametrize("method, suffix", (("GET", ""), ("DELETE", ""),
    ("GET", "/measurements"), ("POST", "/measurements"),
    ("GET", "/measurements/1"), ("DELETE", "/measurements/1")))
@pytest.mark.parametrize("invalid_id", ("invalid", "1.5", "0", "-1", str(2**31), str(2**63)))
def test_resource_routes_reject_invalid_dataset_ids(
    assert_http_error, existing_dataset, method, suffix, invalid_id
):
    kwargs = {"json": {"latency_ms": 100}} if method == "POST" else {}
    assert_http_error(
        method, f"/datasets/{invalid_id}{suffix}", 422, INVALID_REQUEST, **kwargs
    )


@pytest.mark.parametrize("method", ("GET", "DELETE"))
@pytest.mark.parametrize("invalid_id", ("invalid", "1.5", "0", "-1", str(2**31), str(2**63)))
def test_resource_routes_reject_invalid_measurement_ids(
    assert_http_error, existing_dataset, method, invalid_id
):
    assert_http_error(
        method, f"/datasets/{existing_dataset.id}/measurements/{invalid_id}",
        422, INVALID_REQUEST,
    )


@pytest.mark.parametrize("method, suffix", (("GET", ""), ("DELETE", ""),
    ("GET", "/measurements"), ("POST", "/measurements"),
    ("GET", "/measurements/1"), ("DELETE", "/measurements/1")))
def test_missing_dataset_does_not_affect_an_existing_one(
    assert_http_error, existing_dataset, method, suffix
):
    kwargs = {"json": {"latency_ms": 100}} if method == "POST" else {}
    assert_http_error(
        method, f"/datasets/999{suffix}", 404, "Dataset não encontrado.", **kwargs
    )


@pytest.mark.parametrize("method", ("GET", "DELETE"))
def test_missing_measurement_does_not_affect_existing_measurements(
    assert_http_error, existing_dataset, method
):
    assert_http_error(
        method, f"/datasets/{existing_dataset.id}/measurements/999", 404,
        "Medição não encontrada.",
    )


@pytest.mark.parametrize("method", ("GET", "DELETE"))
def test_foreign_measurement_is_rejected_and_both_datasets_are_preserved(
    client, assert_http_error, existing_dataset, method
):
    other = client.post("/datasets", json={"latency_ms": [300, 400]})
    assert other.status_code == 201
    foreign_id = existing_dataset.measurements[0].id
    assert_http_error(
        method, f"/datasets/{other.json()['id']}/measurements/{foreign_id}", 404,
        "Medição não encontrada.",
    )


def test_last_measurement_conflict_preserves_the_persisted_row(
    assert_http_error, single_measurement_dataset, client
):
    path = f"/datasets/{single_measurement_dataset.id}/measurements"
    measurement = client.get(path).json()[0]
    assert_http_error(
        "DELETE", f"{path}/{measurement['id']}", 409,
        "A última medição não pode ser removida.",
    )
    # A sessão continua utilizável após a rejeição.
    assert client.post(path, json={"latency_ms": 200}).status_code == 201
    assert client.delete(f"{path}/{measurement['id']}").status_code == 204


def test_empty_dataset_rejection_preserves_existing_rows(assert_http_error, existing_dataset):
    assert_http_error(
        "POST", "/datasets", 422, "O dataset precisa de pelo menos uma medição.",
        json={"latency_ms": []},
    )


def test_largest_valid_id_is_not_found_rather_than_rejected(assert_http_error):
    assert_http_error("GET", f"/datasets/{2**31 - 1}", 404, "Dataset não encontrado.")
