from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.exceptions import DatasetWouldBecomeEmptyError
from ..domain.latency import LatencyDataset
from ..domain.validation import validate_latency
from ..errors.errors import DatasetNotFoundError, MeasurementNotFoundError
from ..mapper.latency_mapper import (
    model_to_domain,
    model_to_schema,
    schema_to_model,
)
from ..models.datasets_models import LatencyDatasetModel, LatencyMeasurementModel
from ..schemas.latency_dataset_schema import (
    CreateLatencyDatasetSchema,
    ResponseLatencyDatasetSchema,
    ResponseLatencyMeasurementSchema,
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

    def delete_dataset(self, dataset_id: int) -> None:
        model = self._get_model(dataset_id)
        self.db.delete(model)
        self.db.commit()

    def add_measurement(
        self, dataset_id: int, measurement: float
    ) -> ResponseLatencyMeasurementSchema:
        model = self._get_model(dataset_id)
        domain = model_to_domain(model)
        domain.add(measurement)
        created = LatencyMeasurementModel(
            dataset=model,
            position=max(item.position for item in model.measurements) + 1,
            latency_ms=domain.measurements[-1],
        )
        self.db.add(created)
        self.db.commit()
        self.db.refresh(created)
        return ResponseLatencyMeasurementSchema.model_validate(created)

    def remove_measurement(
        self, dataset_id: int, measurement_id: int
    ) -> None:
        model = self._get_model(dataset_id)
        measurement = self._get_measurement(model, measurement_id)
        if len(model.measurements) == 1:
            raise DatasetWouldBecomeEmptyError("A última medição não pode ser removida.")
        self.db.delete(measurement)
        self.db.commit()

    def list_measurements(
        self, dataset_id: int, latency_ms: float | None = None
    ) -> list[ResponseLatencyMeasurementSchema]:
        model = self._get_model(dataset_id)
        value = validate_latency(latency_ms) if latency_ms is not None else None
        return [
            ResponseLatencyMeasurementSchema.model_validate(measurement)
            for measurement in model.measurements
            if value is None or measurement.latency_ms == value
        ]

    def get_measurement(
        self, dataset_id: int, measurement_id: int
    ) -> ResponseLatencyMeasurementSchema:
        model = self._get_model(dataset_id)
        measurement = self._get_measurement(model, measurement_id)
        return ResponseLatencyMeasurementSchema.model_validate(measurement)

    def _get_model(self, dataset_id: int) -> LatencyDatasetModel:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        if model is None:
            raise DatasetNotFoundError()
        return model

    @staticmethod
    def _get_measurement(
        model: LatencyDatasetModel, measurement_id: int
    ) -> LatencyMeasurementModel:
        for measurement in model.measurements:
            if measurement.id == measurement_id:
                return measurement
        raise MeasurementNotFoundError()

    def get_domain(self, dataset_id: int) -> LatencyDataset:
        model = self.db.get(LatencyDatasetModel, dataset_id)
        return model_to_domain(model)
