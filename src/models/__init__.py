"""
Models initialization.
"""

from .admin import StreamStats, StreamStatsResponse, SystemStatsResponse
from .analytics import EventAggregation, RealtimeMetrics
from .database import (
    EventModel,
    AggregationOneMinute,
    AggregationHourly,
    AggregationDaily,
    UserActivity,
)
from .events import (
    Event,
    EventCreate,
    EventBatchCreate,
    EventBatchResponse,
    EventResponse,
)
from .misc import Root200Response, Health200Response

__all__ = [
    "EventModel",
    "AggregationOneMinute",
    "AggregationHourly",
    "AggregationDaily",
    "UserActivity",
    "Root200Response",
    "Health200Response",
    "EventAggregation",
    "RealtimeMetrics",
    "Event",
    "EventCreate",
    "EventBatchCreate",
    "EventBatchResponse",
    "EventResponse",
    "StreamStats",
    "StreamStatsResponse",
    "SystemStatsResponse",
]
