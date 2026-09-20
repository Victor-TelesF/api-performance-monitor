from pydantic import BaseModel, ConfigDict


class CreateLatencyDatasetSchema(BaseModel):
    latency_ms: list[float]

class ResponseLatencyDatasetSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)
    id: int
    latency_ms: list[float]
