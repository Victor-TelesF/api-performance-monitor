"""Rotas para gerar gráficos PNG das medições de um dataset."""

from array import array
from collections.abc import Callable
from functools import partial
from hashlib import blake2b
from math import ceil, sqrt
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Query, Response
from matplotlib.figure import Figure

from ..database import SessionDep
from ..domain import LatencyDataset
from ..domain.exceptions import InvalidLatencyError
from ..schemas.error_schema import ErrorResponseSchema
from ..schemas.path_parameters import ResourceId
from ..services.latency_dataset_service import LatencyDatasetService
from ..visualization import (
    create_cumulative_distribution,
    create_latency_boxplot,
    create_latency_frequency_chart,
    create_latency_histogram,
    create_latency_timeline,
    figure_to_png,
)
from ..visualization.cache import PngCache

MAX_CHART_MEASUREMENTS = 10_000
MAX_HISTOGRAM_BINS = 200
MAX_FREQUENCY_VALUES = 200

router = APIRouter(
    prefix="/datasets/{dataset_id}/charts",
    tags=["Visualizações"],
    default_response_class=Response,
    responses={
        200: {
            "description": "Gráfico das latências em PNG.",
            "content": {"image/png": {"schema": {"type": "string", "format": "binary"}}},
        },
        404: {
            "model": ErrorResponseSchema,
            "description": "Dataset não encontrado.",
        },
        422: {
            "model": ErrorResponseSchema,
            "description": "Dados de entrada ou regra de negócio inválidos.",
        },
    },
)

# As rotas síncronas rodam em threads; o Matplotlib compartilha estado interno.
_render_lock = Lock()
_png_cache = PngCache()


def _png_response(
    dataset: LatencyDataset,
    create_chart: Callable[[LatencyDataset], Figure],
    *,
    chart: str,
    bins: int | None = None,
    show_percentiles: bool = True,
) -> Response:
    """Reutiliza o PNG pelo conteúdo; apenas imagens novas exigem renderização."""
    digest = blake2b(array("d", dataset.measurements).tobytes(), digest_size=32).digest()
    key = (chart, digest, bins, show_percentiles)
    cached = _png_cache.get(key)
    if cached is not None:
        return Response(content=cached, media_type="image/png")
    with _render_lock:
        # Outra thread pode ter renderizado o mesmo conteúdo durante a espera.
        cached = _png_cache.get(key)
        if cached is not None:
            return Response(content=cached, media_type="image/png")
        figure = create_chart(dataset)
        try:
            with figure_to_png(figure) as png:
                content = png.getvalue()
        finally:
            figure.clear()
        _png_cache.put(key, content)
        return Response(content=content, media_type="image/png")


def _chart_dataset(db: SessionDep, dataset_id: int) -> LatencyDataset:
    return LatencyDatasetService(db).get_chart_domain(
        dataset_id, max_measurements=MAX_CHART_MEASUREMENTS
    )


@router.get("/histogram", summary="Gerar histograma das latências")
def latency_histogram(
    dataset_id: ResourceId,
    db: SessionDep,
    bins: Annotated[
        int | None,
        Query(
            ge=1,
            le=MAX_HISTOGRAM_BINS,
            description=(
                "Faixas (1–200); padrão: raiz da quantidade de medições, limitada a 200."
            ),
        ),
    ] = None,
    show_percentiles: bool = True,
) -> Response:
    dataset = _chart_dataset(db, dataset_id)
    effective_bins = (
        bins if bins is not None
        else min(MAX_HISTOGRAM_BINS, ceil(sqrt(dataset.count())))
    )
    return _png_response(
        dataset,
        partial(
            create_latency_histogram,
            bins=effective_bins,
            show_percentiles=show_percentiles,
        ),
        chart="histogram",
        bins=effective_bins,
        show_percentiles=show_percentiles,
    )


@router.get("/boxplot", summary="Gerar boxplot das latências")
def latency_boxplot(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = _chart_dataset(db, dataset_id)
    return _png_response(dataset, create_latency_boxplot, chart="boxplot")


@router.get(
    "/timeline",
    summary="Gerar gráfico por ordem da medição",
    description="O eixo X representa a posição das medições, não horários reais.",
)
def latency_timeline(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = _chart_dataset(db, dataset_id)
    return _png_response(dataset, create_latency_timeline, chart="timeline")


@router.get("/cumulative", summary="Gerar distribuição acumulada das latências")
def cumulative_distribution(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = _chart_dataset(db, dataset_id)
    return _png_response(dataset, create_cumulative_distribution, chart="cumulative")


@router.get("/frequency", summary="Gerar gráfico de frequência das latências")
def latency_frequency(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = _chart_dataset(db, dataset_id)
    if len(set(dataset.measurements)) > MAX_FREQUENCY_VALUES:
        raise InvalidLatencyError(
            f"O gráfico de frequência aceita no máximo {MAX_FREQUENCY_VALUES} "
            "latências distintas; use o histograma."
        )
    return _png_response(dataset, create_latency_frequency_chart, chart="frequency")
