"""
Pydantic models for event validation and serialization.
These models are used for API request/response validation.
"""

from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCategory(str, Enum):
    """Event category enum."""

    USER = "user"
    ACTIVITY = "activity"
    TRANSACTION = "transaction"
    SYSTEM = "system"


class UserEventType(str, Enum):
    """User event types."""

    REGISTERED = "user.registered"
    LOGIN = "user.login"
    LOGOUT = "user.logout"
    PROFILE_UPDATED = "user.profile_updated"


class ActivityEventType(str, Enum):
    """Activity event types."""

    PAGE_VIEW = "activity.page_view"
    CLICK = "activity.click"
    SEARCH = "activity.search"
    FEATURE_USED = "activity.feature_used"


class TransactionEventType(str, Enum):
    """Transaction event types."""

    CREATED = "transaction.created"
    COMPLETED = "transaction.completed"
    FAILED = "transaction.failed"
    REFUNDED = "transaction.refunded"


class SystemEventType(str, Enum):
    """System event types."""

    ERROR = "system.error"
    PERFORMANCE = "system.performance"
    API_CALL = "system.api_call"


class EventMetadata(BaseModel):
    """Event metadata model."""

    model_config = ConfigDict(extra="allow")

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None


class EventBase(BaseModel):
    """Base event model."""

    event_type: Union[
        UserEventType, ActivityEventType, TransactionEventType, SystemEventType
    ] = Field(..., description="Event type (e.g., 'user.login')")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[EventMetadata] = Field(default_factory=EventMetadata)
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EventCreate(EventBase):
    """Model for creating a new event."""

    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp (defaults to current time)",
    )


class Event(EventBase):
    """Complete event model with all fields."""

    model_config = ConfigDict(from_attributes=True)

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventBatchCreate(BaseModel):
    """Model for batch event creation."""

    events: list[EventCreate] = Field(..., min_length=1, max_length=1000)


class EventResponse(BaseModel):
    """Event ingestion response."""

    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    status: str = "accepted"
    timestamp: datetime


class EventBatchResponse(BaseModel):
    """Batch event ingestion response."""

    accepted: int
    rejected: int
    event_ids: list[UUID]


# Specific event models for different categories


class UserRegisteredEvent(EventCreate):
    """User registration event."""

    event_type: str = Field(default=UserEventType.REGISTERED.value, frozen=True)
    properties: Dict[str, Any] = Field(
        ...,
        description="Must include: email, username",
        examples=[{"email": "user@example.com", "username": "john_doe"}],
    )


class UserLoginEvent(EventCreate):
    """User login event."""

    event_type: str = Field(default=UserEventType.LOGIN.value, frozen=True)
    user_id: str = Field(..., description="User ID is required for login events")
    properties: Dict[str, Any] = Field(
        default_factory=dict, examples=[{"login_method": "password", "success": True}]
    )


class ActivityPageViewEvent(EventCreate):
    """Page view event."""

    event_type: str = Field(default=ActivityEventType.PAGE_VIEW.value, frozen=True)
    properties: Dict[str, Any] = Field(
        ...,
        description="Must include: page_url, page_title",
        examples=[{"page_url": "/dashboard", "page_title": "Dashboard"}],
    )


class TransactionCreatedEvent(EventCreate):
    """Transaction created event."""

    event_type: str = Field(default=TransactionEventType.CREATED.value, frozen=True)
    user_id: str = Field(..., description="User ID is required")
    properties: Dict[str, Any] = Field(
        ...,
        description="Must include: transaction_id, amount, currency",
        examples=[{"transaction_id": "txn_123", "amount": 99.99, "currency": "USD"}],
    )


class SystemErrorEvent(EventCreate):
    """System error event."""

    event_type: str = Field(default=SystemEventType.ERROR.value, frozen=True)
    properties: Dict[str, Any] = Field(
        ...,
        description="Must include: error_message, error_code, stack_trace",
        examples=[
            {
                "error_message": "Database connection failed",
                "error_code": "DB_CONN_ERR",
                "stack_trace": "...",
            }
        ],
    )
