"""Rotas de persistência dos datasets e de suas medições de latência."""

from fastapi import APIRouter

from ..database import SessionDep
from ..schemas.error_schema import ErrorResponseSchema
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    LatencyMeasurementSchema,
    ResponseLatencyDatasetSchema,
)
from ..services.latency_dataset_service import LatencyDatasetService

router = APIRouter(
    prefix="/Datasets",
    responses={
        422: {
            "model": ErrorResponseSchema,
            "description": "Dados de entrada ou regra de negócio inválidos.",
        }
    },
)


@router.post(
    "/datasets/create",
    tags=["Datasets"],
    summary="Criar dataset",
    response_model=ResponseLatencyDatasetSchema,
)
def create_dataset(dataset: CreateLatencyDatasetSchema, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.create_dataset(dataset)


@router.get(
    "/datasets/list",
    tags=["Datasets"],
    summary="Listar datasets",
    response_model=list[ResponseLatencyDatasetSchema],
)
def list_datasets(db: SessionDep):
    service = LatencyDatasetService(db)
    return service.list_datasets()


@router.get(
    "/datasets/details/{dataset_id}",
    tags=["Datasets"],
    summary="Consultar um dataset",
    response_model=ResponseLatencyDatasetSchema,
)
def get_dataset(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.get_dataset(dataset_id)


@router.delete(
    "/datasets/delete/{dataset_id}",
    tags=["Datasets"],
    summary="Excluir um dataset",
    response_model=ResponseLatencyDatasetSchema,
)
def delete_dataset(dataset_id: int, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.delete_dataset(dataset_id)


@router.post(
    "/measurements/add/{dataset_id}",
    tags=["Medições"],
    summary="Adicionar uma medição",
    response_model=ResponseLatencyDatasetSchema,
)
def add_measurement(
    dataset_id: int, measurement: LatencyMeasurementSchema, db: SessionDep
):
    service = LatencyDatasetService(db)
    return service.add_measurement(dataset_id, measurement.latency_ms)


@router.delete(
    "/measurements/remove/{dataset_id}",
    tags=["Medições"],
    summary="Remover uma medição",
    response_model=ResponseLatencyDatasetSchema,
)
def remove_measurement(dataset_id: int, measurement: float, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.remove_measurement(dataset_id, measurement)


@router.get(
    "/measurements/contains/{dataset_id}",
    tags=["Medições"],
    summary="Verificar se uma medição existe",
    response_model=bool,
)
def contains_measurement(dataset_id: int, measurement: float, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.get_domain(dataset_id).contains(measurement)


@router.get(
    "/measurements/occurrences/{dataset_id}",
    tags=["Medições"],
    summary="Contar ocorrências de uma medição",
    response_model=int,
)
def count_measurement_occurrences(dataset_id: int, measurement: float, db: SessionDep):
    service = LatencyDatasetService(db)
    return service.get_domain(dataset_id).count_occurrences(measurement)
