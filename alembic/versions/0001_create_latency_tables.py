"""Cria datasets e medições de latência.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria as tabelas, índices e regras existentes nos modelos ORM."""
    op.create_table(
        "latency_datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_latency_datasets_id", "latency_datasets", ["id"])

    op.create_table(
        "latency_measurements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "position > 0", name="ck_latency_measurements_position_positive"
        ),
        sa.CheckConstraint(
            "latency_ms >= 0", name="ck_latency_measurements_latency_non_negative"
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["latency_datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dataset_id", "position", name="uq_latency_measurements_dataset_position"
        ),
    )
    op.create_index("ix_latency_measurements_id", "latency_measurements", ["id"])


def downgrade() -> None:
    """Remove primeiro a tabela filha e depois a tabela de datasets."""
    op.drop_index("ix_latency_measurements_id", table_name="latency_measurements")
    op.drop_table("latency_measurements")
    op.drop_index("ix_latency_datasets_id", table_name="latency_datasets")
    op.drop_table("latency_datasets")
