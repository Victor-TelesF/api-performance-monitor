"""Rotas para consultar estatísticas dos datasets de latência."""

from fastapi import APIRouter

from ..database import SessionDep
from ..schemas.error_schema import ErrorResponseSchema
from ..schemas.latency_dataset_schema import (
    CountStatisticResponseSchema,
    ScalarStatisticResponseSchema,
    ValuesStatisticResponseSchema,
)
from ..services.latency_dataset_service import LatencyDatasetService

router = APIRouter(
    prefix="/statistics",
    tags=["Estatísticas"],
    responses={
        422: {
            "model": ErrorResponseSchema,
            "description": "Dados de entrada ou regra de negócio inválidos.",
        }
    },
)


@router.get(
    "/count/{dataset_id}",
    summary="Consultar quantidade de medições",
    response_model=CountStatisticResponseSchema,
)
def statistics_count(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    count = dataset.count()

    return CountStatisticResponseSchema(value=count)


@router.get(
    "/total/{dataset_id}",
    summary="Consultar soma das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_total(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    total_sum = dataset.total()

    return ScalarStatisticResponseSchema(value=total_sum)


@router.get(
    "/minimum/{dataset_id}",
    summary="Consultar menor latência",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_minimum(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    minimum = dataset.minimum()

    return ScalarStatisticResponseSchema(value=minimum)


@router.get(
    "/maximum/{dataset_id}",
    summary="Consultar maior latência",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_maximum(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    maximum = dataset.maximum()

    return ScalarStatisticResponseSchema(value=maximum)


@router.get(
    "/amplitude/{dataset_id}",
    summary="Consultar amplitude das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_amplitude(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    amplitude = dataset.amplitude()

    return ScalarStatisticResponseSchema(value=amplitude)


@router.get(
    "/mean/{dataset_id}",
    summary="Consultar média das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_mean(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    mean = dataset.mean()

    return ScalarStatisticResponseSchema(value=mean)


@router.get(
    "/median/{dataset_id}",
    summary="Consultar mediana das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_median(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    median = dataset.median()

    return ScalarStatisticResponseSchema(value=median)


@router.get(
    "/mode/{dataset_id}",
    summary="Consultar moda das latências",
    response_model=ValuesStatisticResponseSchema,
)
def statistics_mode(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    mode = dataset.mode()

    return ValuesStatisticResponseSchema(values=mode)


@router.get(
    "/variance/{dataset_id}",
    summary="Consultar variância das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_variance(dataset_id: int, db: SessionDep, sample: bool = False):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    variance = dataset.variance(sample=sample)

    return ScalarStatisticResponseSchema(value=variance)


@router.get(
    "/standard-deviation/{dataset_id}",
    summary="Consultar desvio padrão das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_standard_deviation(
    dataset_id: int, db: SessionDep, sample: bool = False
):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    standard_deviation = dataset.standard_deviation(sample=sample)

    return ScalarStatisticResponseSchema(value=standard_deviation)


@router.get(
    "/first-quartile/{dataset_id}",
    summary="Consultar primeiro quartil das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_first_quartile(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    first_quartile = dataset.first_quartile()

    return ScalarStatisticResponseSchema(value=first_quartile)


@router.get(
    "/second-quartile/{dataset_id}",
    summary="Consultar segundo quartil das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_second_quartile(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    second_quartile = dataset.second_quartile()

    return ScalarStatisticResponseSchema(value=second_quartile)


@router.get(
    "/third-quartile/{dataset_id}",
    summary="Consultar terceiro quartil das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_third_quartile(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    third_quartile = dataset.third_quartile()

    return ScalarStatisticResponseSchema(value=third_quartile)


@router.get(
    "/interquartile-range/{dataset_id}",
    summary="Consultar intervalo interquartil das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_interquartile_range(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    interquartile_range = dataset.interquartile_range()

    return ScalarStatisticResponseSchema(value=interquartile_range)


@router.get(
    "/percentile/{dataset_id}",
    summary="Consultar percentil das latências",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_percentile(dataset_id: int, db: SessionDep, percent: float = 95):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    percentile = dataset.percentile(percent)

    return ScalarStatisticResponseSchema(value=percentile)


@router.get(
    "/outliers/{dataset_id}",
    summary="Consultar possíveis valores atípicos",
    response_model=ValuesStatisticResponseSchema,
)
def statistics_outliers(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    outliers = dataset.outliers()

    return ValuesStatisticResponseSchema(values=outliers)


@router.get(
    "/count-above/{dataset_id}",
    summary="Contar medições acima do limite",
    response_model=CountStatisticResponseSchema,
)
def statistics_count_above(dataset_id: int, db: SessionDep, threshold_ms: float = 120):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    count_above = dataset.count_above(threshold_ms)

    return CountStatisticResponseSchema(value=count_above)


@router.get(
    "/proportion-above/{dataset_id}",
    summary="Consultar proporção acima do limite",
    response_model=ScalarStatisticResponseSchema,
)
def statistics_proportion_above(
    dataset_id: int, db: SessionDep, threshold_ms: float = 120
):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    proportion_above = dataset.proportion_above(threshold_ms)

    return ScalarStatisticResponseSchema(value=proportion_above)


@router.get(
    "/count-at-or-below/{dataset_id}",
    summary="Contar medições até o limite",
    response_model=CountStatisticResponseSchema,
)
def statistics_count_at_or_below(
    dataset_id: int, db: SessionDep, threshold_ms: float = 120
):
    service = LatencyDatasetService(db)
    dataset = service.get_domain(dataset_id)
    count_at_or_below = dataset.count_at_or_below(threshold_ms)

    return CountStatisticResponseSchema(value=count_at_or_below)
