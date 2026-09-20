"""Interface pública do domínio de latências.

Exporta ``LatencyDataset`` e as exceções próprias das regras de medição.
"""

from .exceptions import (
    DatasetWouldBecomeEmptyError,
    DomainError,
    EmptyLatencyDatasetError,
    InsufficientMeasurementsError,
    InvalidLatencyError,
    InvalidPercentileError,
    InvalidThresholdError,
    LatencyNotFoundError,
)
from .latency import LatencyDataset

__all__ = [
    "DatasetWouldBecomeEmptyError",
    "DomainError",
    "EmptyLatencyDatasetError",
    "InsufficientMeasurementsError",
    "InvalidLatencyError",
    "InvalidPercentileError",
    "InvalidThresholdError",
    "LatencyDataset",
    "LatencyNotFoundError",
]
