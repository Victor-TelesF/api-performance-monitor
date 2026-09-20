"""Roteador FastAPI reservado para futuras rotas de latência.

``router`` agrupa rotas com o prefixo ``/``; este módulo ainda não registra
nenhuma operação e, portanto, não devolve respostas por conta própria.
"""

from fastapi import APIRouter
from sqlalchemy import select, delete, insert, update
from ..database import SessionDep

from ..models.datasets_models import LatencyDatasetsModel
from ..schemas.latency_dataset_schema import CreateLatencyDatasetSchema, ResponseLatencyDatasetSchema
from ..mapper.latency_mapper import domain_to_model, model_to_domain, schema_to_domain, schema_to_model, model_to_schema


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
    data = db.query(LatencyDatasetsModel).all()
    lista = [model_to_schema(x) for x in data]
    return lista

@router.get("/datasets/details/{dataset_id}", response_model=list[float])
def datasets_details(id: int, db: SessionDep):
    data = db.get(LatencyDatasetsModel, id)
    return model_to_schema(data).latency_ms

@router.delete("/datasets/delete/{dataset_id}", response_model=str)
def datasets_delete(id: int, db: SessionDep):
    db.execute(delete(LatencyDatasetsModel).where(LatencyDatasetsModel.id == id))
    db.commit()
    return "Deletado com sucesso"

@router.post("measurements/add/{dataset_id}")
def measurements_add(id: int, db: SessionDep):

    return