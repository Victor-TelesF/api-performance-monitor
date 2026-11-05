"""Rotas para gerar gráficos PNG das medições de um dataset."""

from collections.abc import Callable
from functools import partial
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Query, Response
from matplotlib.figure import Figure

from ..database import SessionDep
from ..domain import LatencyDataset
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


def _png_response(
    dataset: LatencyDataset,
    create_chart: Callable[[LatencyDataset], Figure],
) -> Response:
    """Renderiza em memória e libera a figura e o buffer após a conversão."""
    with _render_lock:
        figure = create_chart(dataset)
        try:
            with figure_to_png(figure) as png:
                return Response(content=png.getvalue(), media_type="image/png")
        finally:
            figure.clear()


@router.get("/histogram", summary="Gerar histograma das latências")
def latency_histogram(
    dataset_id: ResourceId,
    db: SessionDep,
    bins: Annotated[
        int | None,
        Query(ge=1, description="Quantidade de faixas; automática quando omitida."),
    ] = None,
    show_percentiles: bool = True,
) -> Response:
    dataset = LatencyDatasetService(db).get_domain(dataset_id)
    return _png_response(
        dataset,
        partial(create_latency_histogram, bins=bins, show_percentiles=show_percentiles),
    )


@router.get("/boxplot", summary="Gerar boxplot das latências")
def latency_boxplot(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = LatencyDatasetService(db).get_domain(dataset_id)
    return _png_response(dataset, create_latency_boxplot)


@router.get(
    "/timeline",
    summary="Gerar gráfico por ordem da medição",
    description="O eixo X representa a posição das medições, não horários reais.",
)
def latency_timeline(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = LatencyDatasetService(db).get_domain(dataset_id)
    return _png_response(dataset, create_latency_timeline)


@router.get("/cumulative", summary="Gerar distribuição acumulada das latências")
def cumulative_distribution(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = LatencyDatasetService(db).get_domain(dataset_id)
    return _png_response(dataset, create_cumulative_distribution)


@router.get("/frequency", summary="Gerar gráfico de frequência das latências")
def latency_frequency(dataset_id: ResourceId, db: SessionDep) -> Response:
    dataset = LatencyDatasetService(db).get_domain(dataset_id)
    return _png_response(dataset, create_latency_frequency_chart)
