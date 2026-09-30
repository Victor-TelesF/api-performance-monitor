from typing import Annotated
from pydantic import BaseModel, ConfigDict, BeforeValidator


def reject_boolean(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("Booleano não é uma latência.")
    return value

LatencyInput = Annotated[float, BeforeValidator(reject_boolean)]


class CreateLatencyDatasetSchema(BaseModel):
    latency_ms: list[LatencyInput]


class ResponseLatencyDatasetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    latency_ms: list[float]


class LatencyMeasurementSchema(BaseModel):
    latency_ms: float


class ScalarStatisticResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    value: float


class CountStatisticResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    value: int


class ValuesStatisticResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    values: list[float]


class ContainsMeasurementResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    contains: bool
