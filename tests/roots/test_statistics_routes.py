"""Contratos de estatísticas com resultados calculados independentemente."""

import pytest


# Estes valores são calculados para [100, 200], sem chamar o domínio como oráculo.
EXPECTED = {
    "count": {"value": 2},
    "total": {"value": 300.0},
    "minimum": {"value": 100.0},
    "maximum": {"value": 200.0},
    "amplitude": {"value": 100.0},
    "mean": {"value": 150.0},
    "median": {"value": 150.0},
    "mode": {"values": []},
    "variance": {"value": 2500.0},
    "standard-deviation": {"value": 50.0},
    "first-quartile": {"value": 125.0},
    "second-quartile": {"value": 150.0},
    "third-quartile": {"value": 175.0},
    "interquartile-range": {"value": 50.0},
    "percentile": {"value": 195.0},
    "outliers": {"values": []},
    "count-above": {"value": 1},
    "proportion-above": {"value": 0.5},
    "count-at-or-below": {"value": 1},
}


def test_list_datasets_returns_persisted_datasets(client, existing_dataset):
    other = client.post("/datasets", json={"latency_ms": [30, 10, 30]}).json()

    response = client.get("/datasets")

    assert response.status_code == 200
    assert sorted(response.json(), key=lambda item: item["id"]) == [
        {"id": existing_dataset.id, "latency_ms": [100.0, 200.0]},
        {"id": other["id"], "latency_ms": [30.0, 10.0, 30.0]},
    ]


@pytest.mark.parametrize("metric_path, expected", EXPECTED.items())
def test_statistic_route_returns_expected_result(
    client, existing_dataset, database_snapshot, metric_path, expected
):
    before = database_snapshot()
    response = client.get(f"/datasets/{existing_dataset.id}/statistics/{metric_path}")

    assert response.status_code == 200
    assert response.json() == expected
    assert database_snapshot() == before


@pytest.mark.parametrize("metric_path", EXPECTED)
def test_statistic_route_returns_not_found_for_unknown_dataset(
    assert_http_error, existing_dataset, metric_path
):
    assert_http_error(
        "GET", f"/datasets/999/statistics/{metric_path}", 404, "Dataset não encontrado."
    )


@pytest.mark.parametrize("metric_path", EXPECTED)
@pytest.mark.parametrize("invalid_id", ("invalid", "0", "-1", str(2**31)))
def test_statistic_route_rejects_malformed_dataset_id(assert_http_error, metric_path, invalid_id):
    assert_http_error(
        "GET", f"/datasets/{invalid_id}/statistics/{metric_path}", 422,
        "Dados de entrada inválidos.",
    )


@pytest.mark.parametrize(
    "metric_path, params, expected",
    (
        ("variance", {"sample": "false"}, 2500.0),
        ("variance", {"sample": "true"}, 5000.0),
        ("standard-deviation", {"sample": "false"}, 50.0),
        ("standard-deviation", {"sample": "true"}, 70.71067811865476),
        ("percentile", {"percent": "50"}, 150.0),
        ("percentile", {"percent": "0"}, 100.0),
        ("percentile", {"percent": "100"}, 200.0),
        ("count-above", {"threshold_ms": "200"}, 0),
        ("proportion-above", {"threshold_ms": "200"}, 0.0),
        ("count-at-or-below", {"threshold_ms": "200"}, 2),
        ("count-above", {"threshold_ms": "0"}, 2),
        ("proportion-above", {"threshold_ms": "0"}, 1.0),
        ("count-at-or-below", {"threshold_ms": "0"}, 0),
    ),
)
def test_statistic_route_uses_query_parameters(
    client, existing_dataset, metric_path, params, expected
):
    response = client.get(
        f"/datasets/{existing_dataset.id}/statistics/{metric_path}", params=params
    )

    assert response.status_code == 200
    assert response.json() == {"value": pytest.approx(expected)}


@pytest.mark.parametrize("metric_path", ("variance", "standard-deviation"))
def test_sample_dispersion_rejects_one_measurement(
    assert_http_error, single_measurement_dataset, client, metric_path
):
    path = f"/datasets/{single_measurement_dataset.id}/statistics/{metric_path}"
    assert_http_error(
        "GET", path, 422,
        "A variância amostral exige pelo menos duas medições.",
        params={"sample": "true"},
    )
    # A mesma medição é suficiente para a fórmula populacional.
    response = client.get(path, params={"sample": "false"})
    assert response.status_code == 200
    assert response.json() == {"value": 0.0}


@pytest.mark.parametrize("metric_path", ("variance", "standard-deviation"))
def test_sample_flag_rejects_invalid_boolean(assert_http_error, existing_dataset, metric_path):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/statistics/{metric_path}",
        422, "Dados de entrada inválidos.", params={"sample": "invalid"},
    )


@pytest.mark.parametrize("percent", ("-1", "101", "nan", "inf", "-inf", "1e9999"))
def test_percentile_rejects_invalid_numeric_values(assert_http_error, existing_dataset, percent):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/statistics/percentile", 422,
        "O percentil deve ser um número entre 0 e 100.", params={"percent": percent},
    )


@pytest.mark.parametrize("metric_path", ("count-above", "proportion-above", "count-at-or-below"))
@pytest.mark.parametrize("threshold", ("-1", "nan", "inf", "-inf", "1e9999"))
def test_threshold_routes_reject_invalid_numeric_values(
    assert_http_error, existing_dataset, metric_path, threshold
):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/statistics/{metric_path}", 422,
        "O limite deve ser um número real, finito e não negativo.",
        params={"threshold_ms": threshold},
    )


@pytest.mark.parametrize(
    "metric_path, param",
    (("percentile", "percent"), ("count-above", "threshold_ms"),
     ("proportion-above", "threshold_ms"), ("count-at-or-below", "threshold_ms")),
)
@pytest.mark.parametrize("invalid", ("invalid", "true", ""))
def test_statistic_routes_reject_nonnumeric_query_parameters(
    assert_http_error, existing_dataset, metric_path, param, invalid
):
    assert_http_error(
        "GET", f"/datasets/{existing_dataset.id}/statistics/{metric_path}", 422,
        "Dados de entrada inválidos.", params={param: invalid},
    )


@pytest.mark.parametrize(
    "metric_path, expected",
    (("mode", {"values": [100.0]}), ("outliers", {"values": [450.0]})),
)
def test_statistic_routes_return_nonempty_values(client, metric_path, expected):
    created = client.post("/datasets", json={"latency_ms": [100, 100, 110, 120, 130, 450]})
    assert created.status_code == 201

    response = client.get(f"/datasets/{created.json()['id']}/statistics/{metric_path}")

    assert response.status_code == 200
    assert response.json() == expected
