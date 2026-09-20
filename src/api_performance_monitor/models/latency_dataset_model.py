from ..database import Base

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, JSON


class LatencyDatasetCreateModel(Base):
    __tablename__ = "latency_dataset_create"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    latency_ms: Mapped[list[float]] = mapped_column(JSON, nullable=False)


class LatencyDatasetStatisticModel(Base):
    __tablename__ = "latency_dataset_statistic"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
