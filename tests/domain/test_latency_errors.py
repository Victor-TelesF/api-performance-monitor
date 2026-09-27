"""Testes das validações e garantias de estado do domínio de latência."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from api_performance_monitor.domain import (
    DatasetWouldBecomeEmptyError,
    DomainError,
    EmptyLatencyDatasetError,
    InsufficientMeasurementsError,
    InvalidLatencyError,
    InvalidPercentileError,
    InvalidThresholdError,
    LatencyDataset,
    LatencyNotFoundError,
)


INVALID_LATENCY_MESSAGE = "A latência deve ser um número real, finito e não negativo."
INVALID_PERCENTILE_MESSAGE = "O percentil deve ser um número entre 0 e 100."
INVALID_THRESHOLD_MESSAGE = "O limite deve ser um número real, finito e não negativo."

INVALID_LATENCIES = (
    pytest.param(-1, id="negative"),
    pytest.param(True, id="boolean"),
    pytest.param("100", id="string"),
    pytest.param(float("nan"), id="float-nan"),
    pytest.param(Decimal("NaN"), id="decimal-nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
    pytest.param(Decimal("-1e-999999"), id="decimal-negative-rounded-to-zero"),
    pytest.param(Decimal("1e999999"), id="decimal-overflow"),
)

INVALID_PERCENTILES = (
    pytest.param(-1, id="below-zero"),
    pytest.param(101, id="above-one-hundred"),
    pytest.param(True, id="boolean"),
    pytest.param("95", id="string"),
    pytest.param(float("nan"), id="float-nan"),
    pytest.param(Decimal("NaN"), id="decimal-nan"),
    pytest.param(float("inf"), id="infinity"),
    pytest.param(Decimal("100.00000000000000000001"), id="decimal-above-one-hundred"),
)

INVALID_THRESHOLDS = (
    pytest.param(-1, id="negative"),
    pytest.param(False, id="boolean"),
    pytest.param("100", id="string"),
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="infinity"),
)


def test_rejects_empty_dataset() -> None:
    """Rejeita a criação de um dataset sem medições."""
    with pytest.raises(EmptyLatencyDatasetError) as error:
        LatencyDataset([])

    assert str(error.value) == "O dataset precisa de pelo menos uma medição."


def test_rejects_non_iterable_measurements() -> None:
    """Rejeita um valor não iterável no lugar da coleção de medições."""
    measurements: Any = 100

    with pytest.raises(InvalidLatencyError) as error:
        LatencyDataset(measurements)

    assert str(error.value) == "As medições devem formar uma coleção de números."


@pytest.mark.parametrize("invalid_latency", INVALID_LATENCIES)
def test_constructor_rejects_each_invalid_latency_category(
    invalid_latency: Any,
) -> None:
    """Rejeita cada categoria de latência inválida durante a construção."""
    with pytest.raises(InvalidLatencyError) as error:
        LatencyDataset([100, invalid_latency])

    assert str(error.value) == INVALID_LATENCY_MESSAGE


def test_latency_validation_accepts_valid_boundary_values() -> None:
    """Aceita zero e valores decimais finitos nas operações do dataset."""
    dataset = LatencyDataset([0, Decimal("0.125")])

    dataset.add(0)

    assert dataset.measurements == (0.0, 0.125, 0.0)
    assert dataset.contains(0) is True
    assert dataset.count_occurrences(0) == 2


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(lambda dataset: dataset.add(-1), id="add"),
        pytest.param(lambda dataset: dataset.remove(-1), id="remove"),
    ),
)
def test_rejected_mutation_preserves_measurements(
    operation: Callable[[LatencyDataset], object],
) -> None:
    """Preserva as medições quando uma adição ou remoção é inválida."""
    dataset = LatencyDataset([100, 200])

    with pytest.raises(InvalidLatencyError) as error:
        operation(dataset)

    assert str(error.value) == INVALID_LATENCY_MESSAGE
    assert dataset.measurements == (100.0, 200.0)


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(lambda dataset: dataset.contains(-1), id="contains"),
        pytest.param(
            lambda dataset: dataset.count_occurrences(-1),
            id="count-occurrences",
        ),
    ),
)
def test_queries_reject_invalid_latency(
    operation: Callable[[LatencyDataset], object],
) -> None:
    """Rejeita latências inválidas nas consultas de existência e ocorrência."""
    dataset = LatencyDataset([100, 200])

    with pytest.raises(InvalidLatencyError) as error:
        operation(dataset)

    assert str(error.value) == INVALID_LATENCY_MESSAGE


def test_removing_missing_latency_preserves_measurements() -> None:
    """Mantém o dataset intacto ao tentar remover uma latência ausente."""
    dataset = LatencyDataset([100, 200])

    with pytest.raises(LatencyNotFoundError) as error:
        dataset.remove(300)

    assert str(error.value) == "A latência 300.0 ms não foi encontrada."
    assert dataset.measurements == (100.0, 200.0)


def test_removing_only_measurement_preserves_dataset() -> None:
    """Impede a remoção da única medição e preserva o dataset."""
    dataset = LatencyDataset([100])

    with pytest.raises(DatasetWouldBecomeEmptyError) as error:
        dataset.remove(100)

    assert str(error.value) == "A última medição não pode ser removida."
    assert dataset.measurements == (100.0,)


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(lambda dataset: dataset.variance(sample=True), id="variance"),
        pytest.param(
            lambda dataset: dataset.standard_deviation(sample=True),
            id="standard-deviation",
        ),
    ),
)
def test_sample_dispersion_requires_two_measurements(
    operation: Callable[[LatencyDataset], object],
) -> None:
    """Exige duas medições para variância e desvio-padrão amostrais."""
    dataset = LatencyDataset([100])

    with pytest.raises(InsufficientMeasurementsError) as error:
        operation(dataset)

    assert str(error.value) == "A variância amostral exige pelo menos duas medições."


@pytest.mark.parametrize("invalid_percentile", INVALID_PERCENTILES)
def test_rejects_each_invalid_percentile_category(invalid_percentile: Any) -> None:
    """Rejeita percentis fora do intervalo ou com tipos e valores inválidos."""
    dataset = LatencyDataset([100, 200])

    with pytest.raises(InvalidPercentileError) as error:
        dataset.percentile(invalid_percentile)

    assert str(error.value) == INVALID_PERCENTILE_MESSAGE


@pytest.mark.parametrize(
    ("percentile", "expected"),
    (
        pytest.param(0, 100.0, id="lower-boundary"),
        pytest.param(100, 200.0, id="upper-boundary"),
    ),
)
def test_percentile_accepts_inclusive_boundaries(
    percentile: int,
    expected: float,
) -> None:
    """Aceita os limites inclusivos de percentil zero e cem."""
    dataset = LatencyDataset([100, 200])

    assert dataset.percentile(percentile) == expected


@pytest.mark.parametrize("invalid_threshold", INVALID_THRESHOLDS)
def test_count_above_rejects_each_invalid_threshold_category(
    invalid_threshold: Any,
) -> None:
    """Rejeita cada categoria de limite inválido na contagem superior."""
    dataset = LatencyDataset([0, 100])

    with pytest.raises(InvalidThresholdError) as error:
        dataset.count_above(invalid_threshold)

    assert str(error.value) == INVALID_THRESHOLD_MESSAGE


@pytest.mark.parametrize(
    "operation",
    (
        pytest.param(
            lambda dataset: dataset.proportion_above(-1),
            id="proportion-above",
        ),
        pytest.param(
            lambda dataset: dataset.count_at_or_below(-1),
            id="count-at-or-below",
        ),
    ),
)
def test_derived_threshold_queries_propagate_validation_error(
    operation: Callable[[LatencyDataset], object],
) -> None:
    """Propaga a validação de limite nas consultas derivadas."""
    dataset = LatencyDataset([0, 100])

    with pytest.raises(InvalidThresholdError) as error:
        operation(dataset)

    assert str(error.value) == INVALID_THRESHOLD_MESSAGE


def test_threshold_validation_accepts_zero_and_uses_strict_comparison() -> None:
    """Aceita limite zero e mantém a semântica estrita de `acima de`."""
    dataset = LatencyDataset([0, 100])

    assert dataset.count_above(0) == 1
    assert dataset.proportion_above(0) == 0.5
    assert dataset.count_at_or_below(0) == 1


def test_all_specific_errors_inherit_from_domain_error() -> None:
    """Garante que todos os erros específicos possam ser tratados como DomainError."""
    error_types = (
        DatasetWouldBecomeEmptyError,
        EmptyLatencyDatasetError,
        InsufficientMeasurementsError,
        InvalidLatencyError,
        InvalidPercentileError,
        InvalidThresholdError,
        LatencyNotFoundError,
    )

    assert all(issubclass(error_type, DomainError) for error_type in error_types)
