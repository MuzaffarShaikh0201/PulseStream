"""
Pydantic models for analytics and aggregations.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    """Time window model for aggregations."""

    start: datetime
    end: datetime
    duration_seconds: int


class EventAggregation(BaseModel):
    """Event aggregation model."""

    event_type: str
    window: TimeWindow
    event_count: int
    unique_users: int
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RealtimeMetrics(BaseModel):
    """Real-time metrics model."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    events_per_second: float
    active_users_1min: int
    active_users_5min: int
    active_users_1hour: int
    top_events: list[Dict[str, Any]]
    error_rate: float
    avg_processing_latency_ms: float


class UserActivitySummary(BaseModel):
    """User activity summary model."""

    user_id: str
    first_seen: datetime
    last_seen: datetime
    total_events: int
    last_event_type: Optional[str] = None
    activity_data: Dict[str, Any] = Field(default_factory=dict)


class EventQueryParams(BaseModel):
    """Event query parameters."""

    event_type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AggregationQueryParams(BaseModel):
    """Aggregation query parameters."""

    event_type: Optional[str] = None
    window_type: str = Field(..., pattern="^(1min|5min|15min|1hour|1day)$")
    start_time: datetime
    end_time: datetime
