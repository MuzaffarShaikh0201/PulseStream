"""
Query API endpoints.
Handles retrieving events and analytics data.
"""

from uuid import UUID
from typing import List
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from ..db import db_manager, get_db
from ..auth import get_api_key
from ..models.events import Event
from ..utils.logging import get_logger
from ..models.database import EventModel, AggregationOneMinute
from ..models.analytics import EventQueryParams, RealtimeMetrics


logger = get_logger(__name__)
router = APIRouter(tags=["Query APIs"])


@router.get(
    path="/events",
    summary="Query events",
    description="Query events with optional filters",
    response_model=List[Event],
    status_code=status.HTTP_200_OK,
)
async def query_events(
    params: EventQueryParams = Depends(EventQueryParams),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> List[Event]:
    """
    Query events with filters.

    Args:
        params: EventQueryParams - Query parameters
        db: AsyncSession - Database session
        api_key: API key
    Returns:
        List of events matching the filters
    """
    try:
        # Build query
        query = select(EventModel)

        # Apply filters
        conditions = []
        if params.event_type:
            conditions.append(EventModel.event_type == params.event_type)
        if params.user_id:
            conditions.append(EventModel.user_id == params.user_id)
        if params.session_id:
            conditions.append(EventModel.session_id == params.session_id)
        if params.start_time:
            conditions.append(EventModel.timestamp >= params.start_time)
        if params.end_time:
            conditions.append(EventModel.timestamp <= params.end_time)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply ordering and pagination
        query = query.order_by(EventModel.timestamp.desc())
        query = query.limit(params.limit).offset(params.offset)

        # Execute query
        result = await db.execute(query)
        events = result.scalars().all()

        # Convert to Pydantic models
        return [
            Event(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.user_id,
                session_id=event.session_id,
                timestamp=event.timestamp,
                metadata=event.event_metadata,
                properties=event.properties,
                created_at=event.created_at,
            )
            for event in events
        ]

    except Exception as e:
        logger.error(f"Failed to query events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query events: {str(e)}",
        )


@router.get(
    path="/events/{event_id}",
    summary="Get event by ID",
    description="Retrieve a specific event by its ID",
    status_code=status.HTTP_200_OK,
    response_model=Event,
)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> Event:
    """
    Get a specific event by ID.

    Args:
        event_id: Event UUID
        db: AsyncSession - Database session
        api_key: API key

    Returns:
        Event - Specific event by ID

    Raises:
        HTTPException: If event not found
    """
    try:
        query = select(EventModel).where(EventModel.event_id == event_id)
        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found",
            )

        return Event(
            event_id=event.event_id,
            event_type=event.event_type,
            user_id=event.user_id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            metadata=event.event_metadata,
            properties=event.properties,
            created_at=event.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event: {str(e)}",
        )


@router.get(
    path="/analytics/realtime",
    summary="Get real-time metrics",
    description="Get current real-time metrics and statistics",
    response_model=RealtimeMetrics,
    status_code=status.HTTP_200_OK,
)
async def get_realtime_metrics(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
) -> RealtimeMetrics:
    """
    Get real-time metrics.

    Calculates current metrics including events per second,
    active users, and top events.

    Args:
        db: AsyncSession - Database session
        api_key: API key

    Returns:
        RealtimeMetrics - Current real-time metrics and statistics
    """
    try:
        now = datetime.now(timezone.utc)
        one_min_ago = now - timedelta(minutes=1)
        five_min_ago = now - timedelta(minutes=5)
        one_hour_ago = now - timedelta(hours=1)

        # Get 1-minute aggregation for events per second
        query_1min = select(func.sum(AggregationOneMinute.event_count)).where(
            AggregationOneMinute.window_start >= one_min_ago
        )
        result = await db.execute(query_1min)
        events_last_min = result.scalar() or 0
        events_per_second = events_last_min / 60.0

        # Get active users counts (from events table)
        # 1 minute
        query = select(func.count(func.distinct(EventModel.user_id))).where(
            and_(EventModel.timestamp >= one_min_ago, EventModel.user_id.isnot(None))
        )
        result = await db.execute(query)
        active_users_1min = result.scalar() or 0

        # 5 minutes
        query = select(func.count(func.distinct(EventModel.user_id))).where(
            and_(EventModel.timestamp >= five_min_ago, EventModel.user_id.isnot(None))
        )
        result = await db.execute(query)
        active_users_5min = result.scalar() or 0

        # 1 hour
        query = select(func.count(func.distinct(EventModel.user_id))).where(
            and_(EventModel.timestamp >= one_hour_ago, EventModel.user_id.isnot(None))
        )
        result = await db.execute(query)
        active_users_1hour = result.scalar() or 0

        # Get top events (last hour)
        query = (
            select(
                EventModel.event_type, func.count(EventModel.event_id).label("count")
            )
            .where(EventModel.timestamp >= one_hour_ago)
            .group_by(EventModel.event_type)
            .order_by(func.count(EventModel.event_id).desc())
            .limit(10)
        )

        result = await db.execute(query)
        top_events = [{"event_type": row[0], "count": row[1]} for row in result.all()]

        # Error rate: system.error events / total events (last hour)
        error_query = select(
            func.count(case((EventModel.event_type == "system.error", 1))).label(
                "error_count"
            ),
            func.count(EventModel.event_id).label("total_count"),
        ).where(EventModel.timestamp >= one_hour_ago)
        result = await db.execute(error_query)
        row = result.one()
        error_count, total_count = row[0] or 0, row[1] or 0
        error_rate = round(error_count / total_count, 4) if total_count > 0 else 0.0

        # Avg processing latency: created_at - timestamp (ingestion latency)
        latency_query = select(
            func.avg(
                func.extract("epoch", EventModel.created_at - EventModel.timestamp)
                * 1000
            )
        ).where(
            and_(
                EventModel.timestamp >= one_hour_ago,
                EventModel.created_at >= EventModel.timestamp,
            )
        )
        result = await db.execute(latency_query)
        avg_latency = result.scalar()
        avg_processing_latency_ms = (
            round(float(avg_latency), 2) if avg_latency is not None else 0.0
        )

        return RealtimeMetrics(
            timestamp=now,
            events_per_second=round(events_per_second, 2),
            active_users_1min=active_users_1min,
            active_users_5min=active_users_5min,
            active_users_1hour=active_users_1hour,
            top_events=top_events,
            error_rate=error_rate,
            avg_processing_latency_ms=avg_processing_latency_ms,
        )

    except Exception as e:
        logger.error(f"Failed to get realtime metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )
