"""Contratos HTTP e geração real dos gráficos PNG dos datasets."""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from matplotlib.image import imread

from api_performance_monitor.models.datasets_models import LatencyDatasetModel
from api_performance_monitor.roots import visualization_root
from main import app

CHARTS = ("histogram", "boxplot", "timeline", "cumulative", "frequency")


@pytest.mark.parametrize("chart", CHARTS)
@pytest.mark.parametrize(
    "dataset_fixture", ("existing_dataset", "single_measurement_dataset")
)
def test_chart_returns_decodable_png_without_changing_measurements(
    client: TestClient, request: pytest.FixtureRequest, chart: str, dataset_fixture: str
) -> None:
    dataset = request.getfixturevalue(dataset_fixture)
    path = f"/datasets/{dataset.id}"
    before = client.get(f"{path}/measurements").json()

    response = client.get(f"{path}/charts/{chart}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    image = imread(BytesIO(response.content), format="png")
    assert image.shape[0] > 0 and image.shape[1] > 0
    assert image[:, :, :3].std() > 0.01
    assert client.get(f"{path}/measurements").json() == before


@pytest.mark.parametrize("chart", CHARTS)
def test_chart_returns_standard_404_for_unknown_dataset(
    client: TestClient, chart: str
) -> None:
    response = client.get(f"/datasets/999/charts/{chart}")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Dataset não encontrado."}


@pytest.mark.parametrize("chart", CHARTS)
@pytest.mark.parametrize("invalid_id", ("invalid", "0", "-1", str(2**31)))
def test_chart_rejects_invalid_dataset_id(client: TestClient, chart: str, invalid_id: str) -> None:
    response = client.get(f"/datasets/{invalid_id}/charts/{chart}")

    assert response.status_code == 422
    assert response.json() == {"detail": "Dados de entrada inválidos."}


@pytest.mark.parametrize(
    "params",
    (
        {"bins": "0"},
        {"bins": "-1"},
        {"bins": "1.5"},
        {"bins": "invalid"},
        {"bins": "true"},
        {"bins": "201"},
        {"show_percentiles": "invalid"},
    ),
)
def test_histogram_rejects_invalid_options(
    client: TestClient, existing_dataset: LatencyDatasetModel, params: dict[str, str]
) -> None:
    response = client.get(
        f"/datasets/{existing_dataset.id}/charts/histogram", params=params
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Dados de entrada inválidos."}


def test_histogram_options_change_the_rendered_image(client: TestClient) -> None:
    dataset = client.post(
        "/datasets", json={"latency_ms": [100, 100, 110, 120, 130, 450]}
    ).json()
    path = f"/datasets/{dataset['id']}/charts/histogram"

    default = client.get(path)
    explicit_defaults = client.get(path, params={"show_percentiles": "true"})
    without_percentiles = client.get(path, params={"show_percentiles": "false"})
    one_bin = client.get(path, params={"bins": 1, "show_percentiles": "false"})

    for response in (default, explicit_defaults, without_percentiles, one_bin):
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    assert default.content == explicit_defaults.content
    assert default.content != without_percentiles.content
    assert without_percentiles.content != one_bin.content


@pytest.mark.parametrize("chart", CHARTS)
def test_openapi_documents_png_and_json_errors(chart: str) -> None:
    operation = app.openapi()["paths"][
        f"/datasets/{{dataset_id}}/charts/{chart}"
    ]["get"]
    responses = operation["responses"]

    assert operation["tags"] == ["Visualizações"]
    assert set(responses) == {"200", "404", "422"}
    assert responses["200"]["content"] == {
        "image/png": {"schema": {"type": "string", "format": "binary"}}
    }
    for status_code in ("404", "422"):
        assert responses[status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorResponseSchema"
        }


@pytest.mark.parametrize(
    "chart, title",
    (("histogram", "Distribuição das latências"),
     ("boxplot", "Boxplot das latências"),
     ("timeline", "Latência por ordem da medição"),
     ("cumulative", "Distribuição acumulada das latências"),
     ("frequency", "Frequência das latências")),
)
def test_route_renders_the_requested_chart_with_persisted_values(client, monkeypatch, chart, title):
    created = client.post("/datasets", json={"latency_ms": [200, 100, 100, 300]})
    assert created.status_code == 201
    captured = []
    original_export = visualization_root.figure_to_png

    def inspect_and_export(figure):
        axes = figure.axes[0]
        captured.append(axes.get_title())
        if chart == "timeline":
            assert list(axes.lines[0].get_xdata()) == [1, 2, 3, 4]
            assert list(axes.lines[0].get_ydata()) == [200, 100, 100, 300]
        elif chart == "frequency":
            assert [tick.get_text() for tick in axes.get_xticklabels()] == ["100", "200", "300"]
            assert [bar.get_height() for bar in axes.patches] == [2, 1, 1]
        elif chart == "cumulative":
            assert list(axes.lines[0].get_xdata()) == [100, 200, 300]
            assert list(axes.lines[0].get_ydata()) == [50, 75, 100]
        elif chart == "histogram":
            assert [line.get_xdata()[0] for line in axes.lines] == pytest.approx([150, 270, 285, 297])
            assert sum(bar.get_height() for bar in axes.patches) == 4
        elif chart == "boxplot":
            # A mediana observada é 150; não basta receber qualquer PNG válido.
            assert any(list(line.get_ydata()) == [150, 150] for line in axes.lines)
        return original_export(figure)

    monkeypatch.setattr(visualization_root, "figure_to_png", inspect_and_export)
    response = client.get(f"/datasets/{created.json()['id']}/charts/{chart}")

    assert response.status_code == 200
    assert captured == [title]
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_cached_chart_refreshes_after_add_remove_and_delete(client, monkeypatch):
    dataset = client.post("/datasets", json={"latency_ms": [100, 200]}).json()
    path = f"/datasets/{dataset['id']}"
    exports = []
    original_export = visualization_root.figure_to_png

    def export(figure):
        exports.append(figure)
        return original_export(figure)

    monkeypatch.setattr(visualization_root, "figure_to_png", export)
    first = client.get(f"{path}/charts/timeline")
    repeated = client.get(f"{path}/charts/timeline")
    assert first.status_code == repeated.status_code == 200
    assert first.content == repeated.content
    assert len(exports) == 1

    added = client.post(f"{path}/measurements", json={"latency_ms": 450}).json()
    changed = client.get(f"{path}/charts/timeline")
    assert changed.status_code == 200
    assert changed.content != first.content
    assert len(exports) == 2

    client.delete(f"{path}/measurements/{added['id']}")
    restored = client.get(f"{path}/charts/timeline")
    assert restored.status_code == 200
    assert restored.content == first.content
    assert len(exports) == 2

    client.delete(path)
    assert client.get(f"{path}/charts/timeline").status_code == 404


@pytest.mark.parametrize("chart", CHARTS)
def test_chart_measurement_limit_rejects_excess_before_rendering(client, monkeypatch, chart):
    monkeypatch.setattr(visualization_root, "MAX_CHART_MEASUREMENTS", 3)
    created = client.post("/datasets", json={"latency_ms": [10, 20, 30]}).json()
    path = f"/datasets/{created['id']}"
    assert client.get(f"{path}/charts/{chart}").status_code == 200
    client.post(f"{path}/measurements", json={"latency_ms": 40})

    def unexpected_render(*args, **kwargs):
        pytest.fail("Não deve renderizar dados acima do limite.")

    monkeypatch.setattr(visualization_root, "_png_response", unexpected_render)
    response = client.get(f"{path}/charts/{chart}")
    assert response.status_code == 422
    assert response.json() == {"detail": "Os gráficos aceitam no máximo 3 medições por dataset."}
    assert client.get(path).json()["latency_ms"] == [10, 20, 30, 40]


def test_frequency_limit_preserves_histogram_as_alternative(client, monkeypatch):
    monkeypatch.setattr(visualization_root, "MAX_FREQUENCY_VALUES", 2)
    created = client.post("/datasets", json={"latency_ms": [10, 10, 20]}).json()
    path = f"/datasets/{created['id']}"
    assert client.get(f"{path}/charts/frequency").status_code == 200
    client.post(f"{path}/measurements", json={"latency_ms": 30})
    response = client.get(f"{path}/charts/frequency")
    assert response.status_code == 422
    assert "latências distintas" in response.json()["detail"]
    assert client.get(f"{path}/charts/histogram").status_code == 200
