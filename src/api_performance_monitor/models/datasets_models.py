from ..database import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON


class LatencyDatasetsModel(Base):
    __tablename__ = "latency_datasets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    measurements: Mapped[list[float]] = mapped_column(JSON, nullable=False)


class LatencyMeasurementsModel(Base):
    __tablename__ = "latency_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("latency_datasets.id"))
    position: Mapped[int] = mapped_column()
    latency_ms: Mapped[float] = mapped_column()