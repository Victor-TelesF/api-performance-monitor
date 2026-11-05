"""Falhas internas devem continuar visíveis, sem serem disfarçadas de validação."""

import pytest
from matplotlib.figure import Figure

from api_performance_monitor.roots import visualization_root
from api_performance_monitor.services.latency_dataset_service import LatencyDatasetService


def test_programming_error_in_statistics_is_not_silenced(client, existing_dataset, monkeypatch):
    failure = RuntimeError("Falha interna simulada.")

    def fail_get_domain(*args):
        raise failure

    monkeypatch.setattr(LatencyDatasetService, "get_domain", fail_get_domain)

    with pytest.raises(RuntimeError) as caught:
        client.get(f"/datasets/{existing_dataset.id}/statistics/mean")

    assert caught.value is failure


def test_chart_rendering_failure_cleans_up_and_allows_next_request(
    client, existing_dataset, monkeypatch, database_snapshot
):
    before = database_snapshot()
    figures = []
    failure = OSError("Falha interna ao renderizar.")

    def fail_savefig(figure, *args, **kwargs):
        figures.append(figure)
        raise failure

    path = f"/datasets/{existing_dataset.id}/charts/histogram"
    with monkeypatch.context() as patch:
        patch.setattr(Figure, "savefig", fail_savefig)
        with pytest.raises(OSError) as caught:
            client.get(path)

    assert caught.value is failure
    assert len(figures) == 1
    assert figures[0].axes == []
    assert database_snapshot() == before
    # Não deixa o teste seguinte pendurado caso a liberação do lock regrida.
    assert visualization_root._render_lock.acquire(blocking=False)
    visualization_root._render_lock.release()
    response = client.get(path)
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
