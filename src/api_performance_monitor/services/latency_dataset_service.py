from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.latency import LatencyDataset
from ..mapper.latency_mapper import (
    model_to_domain,
    model_to_schema,
    schema_to_model,
    update_model_from_domain,
)
from ..models.datasets_models import LatencyDatasetModel
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
)


class LatencyDatasetService:
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(
        self,
        dataset: CreateLatencyDatasetSchema,
    ) -> ResponseLatencyDatasetSchema:
        model = schema_to_model(dataset)

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return model_to_schema(model)

    def list_datasets(self) -> list[ResponseLatencyDatasetSchema]:
        stmt = select(LatencyDatasetModel)
        models = self.db.scalars(stmt).all()

        return [model_to_schema(model) for model in models]

    def get_dataset(self, dataset_id: int) -> ResponseLatencyDatasetSchema:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        return model_to_schema(model)

    def delete_dataset(self, dataset_id: int) -> ResponseLatencyDatasetSchema:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        response = model_to_schema(model)
        self.db.delete(model)
        self.db.commit()
        return response

    def add_measurement(
        self, dataset_id: int, measurement: float
    ) -> ResponseLatencyDatasetSchema:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        domain = model_to_domain(model)
        domain.add(measurement)

        update_model_from_domain(model, domain)

        self.db.commit()
        self.db.refresh(model)
        return model_to_schema(model)

    def remove_measurement(
        self, dataset_id: int, measurement: float
    ) -> ResponseLatencyDatasetSchema:
        model = self.db.get(LatencyDatasetModel, dataset_id)

        domain = model_to_domain(model)
        domain.remove(measurement)

        update_model_from_domain(model, domain)

        self.db.commit()
        self.db.refresh(model)
        return model_to_schema(model)

    def get_domain(self, dataset_id: int) -> LatencyDataset:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        return model_to_domain(model)
