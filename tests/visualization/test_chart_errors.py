"""Testes da validação do número de bins do histograma de latência."""

from typing import Any

import pytest
from matplotlib.figure import Figure

from api_performance_monitor.domain import LatencyDataset
from api_performance_monitor.visualization import create_latency_histogram


@pytest.mark.parametrize(
    "invalid_bins",
    (
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(True, id="true-boolean"),
        pytest.param(False, id="false-boolean"),
        pytest.param(1.5, id="float"),
        pytest.param("10", id="string"),
    ),
)
def test_histogram_rejects_invalid_number_of_bins(invalid_bins: Any) -> None:
    """Rejeita valores de bins que não sejam inteiros positivos."""
    dataset = LatencyDataset([100, 200, 300])

    with pytest.raises(ValueError) as error:
        create_latency_histogram(dataset, bins=invalid_bins)

    assert str(error.value) == "A quantidade de bins deve ser um inteiro positivo."


@pytest.mark.parametrize(
    "valid_bins",
    (
        pytest.param(None, id="automatic"),
        pytest.param(1, id="minimum-explicit-value"),
    ),
)
def test_histogram_accepts_valid_bin_boundaries(valid_bins: int | None) -> None:
    """Aceita a seleção automática e o menor número explícito de bins."""
    dataset = LatencyDataset([100, 200, 300])

    figure = create_latency_histogram(dataset, bins=valid_bins)

    assert isinstance(figure, Figure)
    assert len(figure.axes) == 1
    figure.clear()
