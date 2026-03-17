"""initial schema with events and aggregations

Revision ID: 64660327c5d2
Revises:
Create Date: 2026-02-28 18:40:58.428400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "64660327c5d2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Parent events table (partitioned by timestamp)
    op.execute("""
        CREATE TABLE events (
            event_id UUID NOT NULL DEFAULT gen_random_uuid(),
            event_type VARCHAR(100) NOT NULL,
            user_id VARCHAR(100),
            session_id VARCHAR(100),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            metadata JSONB,
            properties JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)
    op.execute("CREATE INDEX idx_events_type_timestamp ON events (event_type, timestamp)")
    op.execute("CREATE INDEX idx_events_user_timestamp ON events (user_id, timestamp)")
    op.execute("CREATE INDEX idx_events_metadata_gin ON events USING gin (metadata)")
    op.execute("CREATE INDEX idx_events_properties_gin ON events USING gin (properties)")

    # Partitions for 2026 (Jan–Dec)
    for month in range(1, 13):
        start = f"2026-{month:02d}-01"
        end_month = month + 1 if month < 12 else 1
        end_year = 2026 if month < 12 else 2027
        end = f"{end_year}-{end_month:02d}-01"
        op.execute(f"""
            CREATE TABLE events_2026_{month:02d} PARTITION OF events
            FOR VALUES FROM ('{start}') TO ('{end}')
        """)

    # Aggregation tables
    op.create_table(
        "aggregations_1min",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_users", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agg_1min_type_window", "aggregations_1min", ["event_type", "window_start"])
    op.create_index(
        "idx_agg_1min_unique",
        "aggregations_1min",
        ["event_type", "window_start"],
        unique=True,
    )

    op.create_table(
        "aggregations_hourly",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("hour", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_users", sa.Integer(), nullable=True),
        sa.Column("avg_processing_time_ms", sa.Numeric(10, 2), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agg_hourly_type_hour", "aggregations_hourly", ["event_type", "hour"])
    op.create_index(
        "idx_agg_hourly_unique",
        "aggregations_hourly",
        ["event_type", "hour"],
        unique=True,
    )

    op.create_table(
        "aggregations_daily",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_users", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agg_daily_type_date", "aggregations_daily", ["event_type", "date"])
    op.create_index(
        "idx_agg_daily_unique",
        "aggregations_daily",
        ["event_type", "date"],
        unique=True,
    )

    op.create_table(
        "user_activity",
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_event_type", sa.String(100), nullable=True),
        sa.Column("activity_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("idx_user_activity_last_seen", "user_activity", ["last_seen"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_activity")
    op.drop_table("aggregations_daily")
    op.drop_table("aggregations_hourly")
    op.drop_table("aggregations_1min")
    op.drop_table("events")
