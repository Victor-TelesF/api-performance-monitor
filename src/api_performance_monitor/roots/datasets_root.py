"""Recursos HTTP de datasets e medições de latência."""

from fastapi import APIRouter, Request, Response, status

from ..database import SessionDep
from ..schemas.error_schema import ErrorResponseSchema
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    LatencyMeasurementSchema,
    ResponseLatencyDatasetSchema,
    ResponseLatencyMeasurementSchema,
)
from ..services.latency_dataset_service import LatencyDatasetService

router = APIRouter(
    prefix="/datasets",
    responses={
        422: {
            "model": ErrorResponseSchema,
            "description": "Dados de entrada ou regra de negócio inválidos.",
        }
    },
)

NOT_FOUND = {
    404: {"model": ErrorResponseSchema, "description": "Recurso não encontrado."}
}


@router.post(
    "",
    tags=["Datasets"],
    summary="Criar dataset",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseLatencyDatasetSchema,
)
def create_dataset(
    dataset: CreateLatencyDatasetSchema,
    db: SessionDep,
    request: Request,
    response: Response,
):
    created = LatencyDatasetService(db).create_dataset(dataset)
    response.headers["Location"] = str(
        request.url_for("get_dataset", dataset_id=created.id)
    )
    return created


@router.get(
    "",
    tags=["Datasets"],
    summary="Listar datasets",
    response_model=list[ResponseLatencyDatasetSchema],
)
def list_datasets(db: SessionDep):
    return LatencyDatasetService(db).list_datasets()


@router.get(
    "/{dataset_id}",
    tags=["Datasets"],
    summary="Consultar um dataset",
    response_model=ResponseLatencyDatasetSchema,
    responses=NOT_FOUND,
)
def get_dataset(dataset_id: int, db: SessionDep):
    return LatencyDatasetService(db).get_dataset(dataset_id)


@router.delete(
    "/{dataset_id}",
    tags=["Datasets"],
    summary="Excluir um dataset",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_dataset(dataset_id: int, db: SessionDep) -> None:
    LatencyDatasetService(db).delete_dataset(dataset_id)


@router.post(
    "/{dataset_id}/measurements",
    tags=["Medições"],
    summary="Adicionar uma medição",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseLatencyMeasurementSchema,
    responses=NOT_FOUND,
)
def add_measurement(
    dataset_id: int,
    measurement: LatencyMeasurementSchema,
    db: SessionDep,
    request: Request,
    response: Response,
):
    created = LatencyDatasetService(db).add_measurement(
        dataset_id, measurement.latency_ms
    )
    response.headers["Location"] = str(
        request.url_for(
            "get_measurement", dataset_id=dataset_id, measurement_id=created.id
        )
    )
    return created


@router.get(
    "/{dataset_id}/measurements",
    tags=["Medições"],
    summary="Listar medições, opcionalmente por latência",
    response_model=list[ResponseLatencyMeasurementSchema],
    responses=NOT_FOUND,
)
def list_measurements(dataset_id: int, db: SessionDep, latency_ms: float | None = None):
    return LatencyDatasetService(db).list_measurements(dataset_id, latency_ms)


@router.get(
    "/{dataset_id}/measurements/{measurement_id}",
    tags=["Medições"],
    summary="Consultar uma medição",
    response_model=ResponseLatencyMeasurementSchema,
    responses=NOT_FOUND,
)
def get_measurement(dataset_id: int, measurement_id: int, db: SessionDep):
    return LatencyDatasetService(db).get_measurement(dataset_id, measurement_id)


@router.delete(
    "/{dataset_id}/measurements/{measurement_id}",
    tags=["Medições"],
    summary="Remover uma medição",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **NOT_FOUND,
        409: {
            "model": ErrorResponseSchema,
            "description": "A última medição não pode ser removida.",
        },
    },
)
def remove_measurement(dataset_id: int, measurement_id: int, db: SessionDep) -> None:
    LatencyDatasetService(db).remove_measurement(dataset_id, measurement_id)
