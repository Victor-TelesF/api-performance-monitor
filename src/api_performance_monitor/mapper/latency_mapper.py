"""Conversões entre schemas HTTP, objetos de domínio e modelos ORM."""

from ..domain.latency import LatencyDataset
from ..errors.errors import DatasetNotFoundError
from ..models.datasets_models import LatencyDatasetModel, LatencyMeasurementModel
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
)


def schema_to_domain(data: CreateLatencyDatasetSchema) -> LatencyDataset:
    """Devolve um ``LatencyDataset`` validado a partir das latências do pedido.

    Erros por lista vazia ou valores inválidos são propagados do domínio.
    """
    return LatencyDataset(data.latency_ms)


def domain_to_model(dataset: LatencyDataset) -> LatencyDatasetModel:
    """Converte um dataset do domínio em um novo conjunto de modelos ORM.

    Cria um ``LatencyDatasetModel`` e uma linha ``LatencyMeasurementModel``
    para cada valor do domínio. As posições começam em 1 e preservam a
    ordem das medições. O objeto devolvido ainda não foi salvo no banco.
    """
    measurements = [
        LatencyMeasurementModel(position=position, latency_ms=latency)
        for position, latency in enumerate(dataset.measurements, start=1)
    ]
    return LatencyDatasetModel(measurements=measurements)


def model_to_domain(model: LatencyDatasetModel | None) -> LatencyDataset:
    """Reconstrói e devolve um ``LatencyDataset`` a partir dos modelos ORM.

    Lê ``latency_ms`` das medições relacionadas na ordem definida por
    ``position``. Lança ``DatasetNotFoundError`` quando a busca no banco
    retornou ``None``.
    """
    if model is None:
        raise DatasetNotFoundError()
    return LatencyDataset(
        measurement.latency_ms for measurement in model.measurements
    )


def schema_to_model(data: CreateLatencyDatasetSchema) -> LatencyDatasetModel:
    """Devolve novos modelos ORM após validar o pedido no domínio.

    Combina ``schema_to_domain`` e ``domain_to_model``; não salva no banco.
    """
    return domain_to_model(schema_to_domain(data))


def model_to_schema(model: LatencyDatasetModel | None) -> ResponseLatencyDatasetSchema:
    """Converte um dataset persistido no schema devolvido pela API.

    Reúne as linhas filhas em ``latency_ms``, preservando a ordem delas, e
    inclui o ID do dataset. Lança ``DatasetNotFoundError`` se ``model`` é
    ``None``. O ID precisa ter sido atribuído pelo banco antes da conversão.
    """
    if model is None:
        raise DatasetNotFoundError()

    dataset = model_to_domain(model)
    return ResponseLatencyDatasetSchema(
        id=model.id,
        latency_ms=list(dataset.measurements),
    )


def update_model_from_domain(
    model: LatencyDatasetModel | None, dataset: LatencyDataset
) -> LatencyDatasetModel:
    """Sincroniza as medições persistidas com o dataset e devolve o modelo.

    As linhas existentes são atualizadas pela posição, novas medições são
    acrescentadas e as linhas excedentes são retiradas da relação. Com
    ``delete-orphan``, o SQLAlchemy apaga essas linhas no próximo flush. O
    mapper não executa ``flush`` nem ``commit``. Lança
    ``DatasetNotFoundError`` se ``model`` é ``None``.
    """
    if model is None:
        raise DatasetNotFoundError()

    latencies = dataset.measurements
    shared_length = min(len(model.measurements), len(latencies))

    for index in range(shared_length):
        measurement = model.measurements[index]
        measurement.position = index + 1
        measurement.latency_ms = latencies[index]

    for position, latency in enumerate(
        latencies[shared_length:], start=shared_length + 1
    ):
        model.measurements.append(
            LatencyMeasurementModel(position=position, latency_ms=latency)
        )

    del model.measurements[len(latencies):]
    return model
