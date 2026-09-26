"""Rotas de persistência dos datasets e de suas medições de latência."""

from fastapi import APIRouter
from sqlalchemy import select

from ..database import SessionDep
from ..mapper.latency_mapper import (
    model_to_domain,
    model_to_schema,
    schema_to_model,
    update_model_from_domain,
)
from ..models.datasets_models import LatencyDatasetModel
from ..schemas.latency_dataset_schema import (
    AddLatencyMeasurementSchema,
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
)


router = APIRouter(prefix="/Datasets")


@router.post(
    "/datasets/create",
    tags=["Datasets"],
    summary="Criar dataset",
    response_model=ResponseLatencyDatasetSchema,
)
def create_dataset(dataset: CreateLatencyDatasetSchema, db: SessionDep):
    model = schema_to_model(dataset)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model_to_schema(model)


@router.get(
    "/datasets/list",
    tags=["Datasets"],
    summary="Listar datasets",
    response_model=list[ResponseLatencyDatasetSchema],
)
def datasets_list(db: SessionDep):
    stmt = select(LatencyDatasetModel)
    model = db.scalars(stmt).all()
    return [model_to_schema(dataset) for dataset in model]


@router.get(
    "/datasets/details/{dataset_id}",
    tags=["Datasets"],
    summary="Consultar um dataset",
    response_model=ResponseLatencyDatasetSchema,
)
def datasets_details(dataset_id: int, db: SessionDep):
    model = db.get(LatencyDatasetModel, dataset_id)
    return model_to_schema(model)


@router.delete(
    "/datasets/delete/{dataset_id}",
    tags=["Datasets"],
    summary="Excluir um dataset",
    response_model=str,
)
def datasets_delete(dataset_id: int, db: SessionDep):
    model = db.get(LatencyDatasetModel, dataset_id)
    response = model_to_schema(model)
    db.delete(model)
    db.commit()
    return f"Dataset deletado com sucesso: {response}"


@router.post(
    "/measurements/add/{dataset_id}",
    tags=["Medições"],
    summary="Adicionar uma medição",
    response_model=ResponseLatencyDatasetSchema,
)
def measurements_add(
    dataset_id: int, measurement: AddLatencyMeasurementSchema, db: SessionDep
):
    model = db.get(LatencyDatasetModel, dataset_id)
    domain = model_to_domain(model)
    domain.add(measurement.latency_ms)

    update_model_from_domain(model, domain)

    db.commit()
    db.refresh(model)
    return model_to_schema(model)


@router.delete(
    "/measurements/remove/{dataset_id}",
    tags=["Medições"],
    summary="Remover uma medição",
    response_model=ResponseLatencyDatasetSchema,
)
def measurements_remove(dataset_id: int, measurement: float, db: SessionDep):
    model = db.get(LatencyDatasetModel, dataset_id)

    domain = model_to_domain(model)
    domain.remove(measurement)

    update_model_from_domain(model, domain)

    db.commit()
    db.refresh(model)

    return model_to_schema(model)


@router.get(
    "/measurements/contains/{dataset_id}",
    tags=["Medições"],
    summary="Verificar se uma medição existe",
    response_model=bool,
)
def measurements_contains(dataset_id: int, measurement: float, db: SessionDep):
    model = db.get(LatencyDatasetModel, dataset_id)
    domain = model_to_domain(model)
    return domain.contains(measurement)


@router.get(
    "/measurements/occurrences/{dataset_id}",
    tags=["Medições"],
    summary="Contar ocorrências de uma medição",
    response_model=int,
)
def measurements_occurrences(dataset_id: int, measurement: float, db: SessionDep):
    model = db.get(LatencyDatasetModel, dataset_id)
    domain = model_to_domain(model)
    return domain.count_occurrences(measurement)
