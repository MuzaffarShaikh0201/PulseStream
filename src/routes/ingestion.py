"""
Event ingestion API endpoints.
Handles receiving and publishing events to Redis Streams.
"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import get_api_key
from ..models import (
    Event,
    EventBatchCreate,
    EventBatchResponse,
    EventResponse,
    EventCreate,
)
from ..services import event_producer
from ..utils.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["Ingestion APIs"])


@router.post(
    path="/events",
    summary="Ingest single event",
    description="Ingest a single event into the processing pipeline",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventResponse,
)
async def ingest_event(
    request: Request, event_data: EventCreate, api_key: str = Depends(get_api_key)
) -> EventResponse:
    """
    Ingest a single event.

    The event is validated, assigned an ID, and published to the appropriate
    Redis Stream based on its event type.

    Args:
        request: FastAPI request
        event_data: Event data to ingest
        api_key: API key for authentication

    Returns:
        EventResponse with event_id and status

    Raises:
        HTTPException: If event publishing fails
    """
    try:
        # Create Event object with generated ID
        event = Event(
            event_id=uuid4(),
            event_type=event_data.event_type,
            user_id=event_data.user_id,
            session_id=event_data.session_id,
            timestamp=event_data.timestamp or datetime.now(timezone.utc),
            metadata=event_data.metadata,
            properties=event_data.properties,
            created_at=datetime.now(timezone.utc),
        )

        # Publish to Redis Stream
        await event_producer.publish_event(event)

        logger.info(
            f"Event ingested: {event.event_id} | Type: {event.event_type} | "
            f"User: {event.user_id} | API Key: {api_key[:10] if api_key else 'none'}"
        )

        return EventResponse(
            event_id=event.event_id,
            status="accepted",
            timestamp=event.timestamp,
        )

    except Exception as e:
        logger.error(f"Failed to ingest event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}",
        )


@router.post(
    path="/events/batch",
    summary="Ingest multiple events",
    description="Ingest multiple events in a single batch for better performance",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventBatchResponse,
)
async def ingest_events_batch(
    request: Request, batch: EventBatchCreate, api_key: str = Depends(get_api_key)
) -> EventBatchResponse:
    """
    Ingest multiple events in a batch.

    This endpoint is optimized for high-throughput ingestion by using
    Redis pipelining to publish multiple events efficiently.

    Args:
        request: FastAPI request
        batch: Batch of events to ingest
        api_key: API key for authentication

    Returns:
        EventBatchResponse with counts and event IDs

    Raises:
        HTTPException: If batch publishing fails
    """
    try:
        # Create Event objects with generated IDs
        events: List[Event] = []
        event_ids: List[str] = []

        for event_data in batch.events:
            event = Event(
                event_id=uuid4(),
                event_type=event_data.event_type,
                user_id=event_data.user_id,
                session_id=event_data.session_id,
                timestamp=event_data.timestamp or datetime.now(timezone.utc),
                metadata=event_data.metadata,
                properties=event_data.properties,
                created_at=datetime.now(timezone.utc),
            )
            events.append(event)
            event_ids.append(str(event.event_id))

        # Publish batch to Redis Streams
        await event_producer.publish_events_batch(events)

        logger.info(
            f"Batch ingested: {len(events)} events | "
            f"API Key: {api_key[:10] if api_key else 'none'}"
        )

        return EventBatchResponse(
            accepted=len(events),
            rejected=0,
            event_ids=event_ids,
        )

    except Exception as e:
        logger.error(f"Failed to ingest batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest batch: {str(e)}",
        )
