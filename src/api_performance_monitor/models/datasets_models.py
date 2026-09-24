from ..database import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, INTEGER, FLOAT, CheckConstraint, UniqueConstraint


class LatencyDatasetModel(Base):
    __tablename__ = "latency_datasets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    measurements: Mapped[list["LatencyMeasurementModel"]] = relationship(back_populates="dataset", order_by="LatencyMeasurementModel.position", cascade="all, delete-orphan")


class LatencyMeasurementModel(Base):
    __tablename__ = "latency_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("latency_datasets.id"))
    position: Mapped[int] = mapped_column(INTEGER, nullable=False)
    latency_ms: Mapped[float] = mapped_column(FLOAT, nullable=False)
    dataset: Mapped["LatencyDatasetModel"] = relationship(back_populates="measurements")

    __table_args__ = (

        CheckConstraint(
            'position > 0',
            name='ck_latency_measurements_position_positive'
        ),
        CheckConstraint(
            'latency_ms >= 0',
            name='ck_latency_measurements_latency_non_negative'
        ),
        UniqueConstraint(
            'dataset_id',
            'position',
            name='uq_latency_measurements_dataset_position'

        )
    )