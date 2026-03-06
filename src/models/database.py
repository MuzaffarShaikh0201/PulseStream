"""
SQLAlchemy database models for PostgreSQL.
Time-series optimized with partitioning support.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class EventModel(Base):
    """
    Events table - partitioned by timestamp.
    Stores all raw events.
    """

    __tablename__ = "events"

    event_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), server_default=text("gen_random_uuid()"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True  # Column name in database  # Changed from JSON to JSONB
    )
    properties: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # Changed from JSON to JSONB
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        # Composite primary key including partition key
        PrimaryKeyConstraint("event_id", "timestamp"),
        Index("idx_events_type_timestamp", "event_type", "timestamp"),
        Index("idx_events_user_timestamp", "user_id", "timestamp"),
        Index("idx_events_metadata_gin", "metadata", postgresql_using="gin"),
        Index("idx_events_properties_gin", "properties", postgresql_using="gin"),
        {
            "postgresql_partition_by": "RANGE (timestamp)",
        },
    )


class AggregationOneMinute(Base):
    """
    1-minute aggregations table.
    Stores pre-computed metrics for 1-minute windows.
    """

    __tablename__ = "aggregations_1min"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Changed from JSON to JSONB
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("idx_agg_1min_type_window", "event_type", "window_start"),
        Index("idx_agg_1min_unique", "event_type", "window_start", unique=True),
    )


class AggregationHourly(Base):
    """
    Hourly aggregations table.
    Stores pre-computed metrics for hourly windows.
    """

    __tablename__ = "aggregations_hourly"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_processing_time_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Changed from JSON to JSONB
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("idx_agg_hourly_type_hour", "event_type", "hour"),
        Index("idx_agg_hourly_unique", "event_type", "hour", unique=True),
    )


class AggregationDaily(Base):
    """
    Daily aggregations table.
    Stores pre-computed metrics for daily windows.
    """

    __tablename__ = "aggregations_daily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Changed from JSON to JSONB
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index("idx_agg_daily_type_date", "event_type", "date"),
        Index("idx_agg_daily_unique", "event_type", "date", unique=True),
    )


class UserActivity(Base):
    """
    User activity summary table.
    Tracks user-level metrics and activity.
    """

    __tablename__ = "user_activity"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activity_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # Changed from JSON to JSONB
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (Index("idx_user_activity_last_seen", "last_seen"),)
