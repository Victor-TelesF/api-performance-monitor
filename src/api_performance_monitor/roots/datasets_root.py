"""Rotas de persistência dos datasets e de suas medições de latência."""

from fastapi import APIRouter

from ..database import SessionDep
from ..errors.errors import DatasetNotFoundError
from ..mapper.latency_mapper import model_to_schema, schema_to_model
from ..models.datasets_models import LatencyDatasetModel
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
)


router = APIRouter(prefix="/Datasets")


@router.post("/datasets/create", response_model=CreateLatencyDatasetSchema)
def create_dataset(dataset: CreateLatencyDatasetSchema, db: SessionDep):
    data = schema_to_model(dataset)
    db.add(data)
    db.commit()
    db.refresh(data)
    return dataset


@router.get("/datasets/list", response_model=list[ResponseLatencyDatasetSchema])
def datasets_list(db: SessionDep):
    data = db.query(LatencyDatasetModel).all()
    return [model_to_schema(model) for model in data]


@router.get("/datasets/details/{dataset_id}", response_model=list[float])
def datasets_details(dataset_id: int, db: SessionDep):
    data = db.get(LatencyDatasetModel, dataset_id)
    return model_to_schema(data).latency_ms


@router.delete("/datasets/delete/{dataset_id}", response_model=str)
def datasets_delete(dataset_id: int, db: SessionDep):
    data = db.get(LatencyDatasetModel, dataset_id)
    if data is None:
        raise DatasetNotFoundError(dataset_id)

    db.delete(data)
    db.commit()
    return "Deletado com sucesso"


@router.post("/measurements/add/{dataset_id}")
def measurements_add(dataset_id: int, db: SessionDep):
    return
