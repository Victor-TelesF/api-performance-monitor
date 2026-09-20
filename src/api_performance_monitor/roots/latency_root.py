"""Roteador FastAPI reservado para futuras rotas de latência.

``router`` agrupa rotas com o prefixo ``/``; este módulo ainda não registra
nenhuma operação e, portanto, não devolve respostas por conta própria.
"""

from fastapi import APIRouter
from ..database import SessionDep

from ..domain.latency import LatencyDataset
from ..models.latency_dataset_model import LatencyDatasetCreateModel
from ..schemas.latency_dataset_schema import CreateLatencyDatasetSchema, ResponseLatencyDatasetSchema
from ..mapper.latency_mapper import domain_to_model, model_to_domain, schema_to_domain, schema_to_model, model_to_schema


router = APIRouter(prefix="/Latency-Dataset")

@router.post("/create-Dataset")
def create_dataset(dataset: CreateLatencyDatasetSchema, db: SessionDep):
    data = schema_to_model(dataset)
    db.add(data)
    db.commit()
    db.refresh(data)
    return dataset

@router.get("/max/{id}")
def max(id: int, db: SessionDep):
    data = db.get(LatencyDatasetCreateModel, id)
    dataset = model_to_domain(data)
    return dataset.maximum()

@router.get("/lista-ms", response_model=list[ResponseLatencyDatasetSchema])
def lista_ms(db: SessionDep):
    data = db.query(LatencyDatasetCreateModel).all()
    lista = [model_to_schema(x) for x in data]
    return lista