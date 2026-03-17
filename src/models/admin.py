"""
Pydantic models for admin API responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StreamStats(BaseModel):
    """Per-stream statistics."""

    stream_key: str
    length: int = 0
    first_entry_id: Optional[str] = None
    last_entry_id: Optional[str] = None
    groups: int = 0
    error: Optional[str] = None


class StreamStatsResponse(BaseModel):
    """Redis Streams statistics response."""

    total_streams: int = 0
    total_messages: int = 0
    total_consumers: int = 0
    total_pending_messages: int = 0
    total_backlog: int = 0
    streams: List[StreamStats] = Field(default_factory=list)


class SystemStatsResponse(BaseModel):
    """System-wide statistics response."""

    total_events: int = 0
    total_users: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    streams: StreamStatsResponse = Field(default_factory=StreamStatsResponse)
    aggregations_1min_count: int = 0
    aggregations_hourly_count: int = 0
    aggregations_daily_count: int = 0
