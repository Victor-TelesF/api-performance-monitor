from pydantic import BaseModel, ConfigDict


class CreateLatencyDatasetSchema(BaseModel):
    latency_ms: list[float]


class ResponseLatencyDatasetSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)
    id: int
    latency_ms: list[float]


class AddLatencyMeasurementSchema(BaseModel):
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