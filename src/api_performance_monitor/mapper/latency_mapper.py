"""Conversões entre o pedido HTTP, o domínio e a linha de persistência."""

from ..domain.latency import LatencyDataset
from ..errors import DatasetNotFoundError
from ..models.latency_dataset_model import LatencyDatasetCreateModel
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
)


def schema_to_domain(data: CreateLatencyDatasetSchema) -> LatencyDataset:
    """Devolve um ``LatencyDataset`` validado a partir das latências do pedido.

    Erros por lista vazia ou valores inválidos são propagados do domínio.
    """
    return LatencyDataset(data.latency_ms)


def domain_to_model(dataset: LatencyDataset) -> LatencyDatasetCreateModel:
    """Devolve uma nova linha ORM com cópia das medições; não salva no banco."""
    return LatencyDatasetCreateModel(latency_ms=list(dataset.measurements))


def model_to_domain(model: LatencyDatasetCreateModel | None) -> LatencyDataset:
    """Devolve um ``LatencyDataset`` reconstruído da linha recebida.

    Lança ``DatasetNotFoundError`` quando a busca no banco retornou ``None``.
    """
    if model is None:
        raise DatasetNotFoundError()
    return LatencyDataset(model.latency_ms)


def schema_to_model(data: CreateLatencyDatasetSchema) -> LatencyDatasetCreateModel:
    """Devolve uma nova linha ORM após validar o pedido no domínio.

    Combina ``schema_to_domain`` e ``domain_to_model``; não salva no banco.
    """
    return domain_to_model(schema_to_domain(data))


def model_to_schema(model: LatencyDatasetCreateModel | None) -> ResponseLatencyDatasetSchema:
    """Devolve o schema de resposta com o ID e as latências de uma linha salva.

    Lança ``DatasetNotFoundError`` se ``model`` é ``None``. O ID precisa ter
    sido atribuído pelo banco antes desta conversão.
    """
    if model is None:
        raise DatasetNotFoundError()
    return ResponseLatencyDatasetSchema.model_validate(model)


def update_model_from_domain(
    model: LatencyDatasetCreateModel | None, dataset: LatencyDataset
) -> LatencyDatasetCreateModel:
    """Substitui a lista JSON de uma linha existente e devolve a mesma linha.

    Atribuir uma lista nova permite ao SQLAlchemy detectar a mudança. O mapper
    não faz ``commit``; a sessão que carregou ``model`` continua responsável
    por persistir a alteração. Lança erro se ``model`` é ``None``.
    """
    if model is None:
        raise DatasetNotFoundError()
    model.latency_ms = list(dataset.measurements)
    return model
