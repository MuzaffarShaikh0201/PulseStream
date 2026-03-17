"""
Admin API endpoints.
Handles monitoring, statistics, and administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import require_admin
from ..db import db_manager, get_db
from ..models.admin import StreamStatsResponse, SystemStatsResponse
from ..models.database import (
    AggregationDaily,
    AggregationHourly,
    AggregationOneMinute,
    EventModel,
    UserActivity,
)
from ..services.producer import event_producer
from ..utils.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["Admin APIs"])


@router.get(
    path="/stats",
    summary="Get system statistics",
    description="Get overall system statistics and health metrics",
    status_code=status.HTTP_200_OK,
    response_model=SystemStatsResponse,
)
async def get_system_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(require_admin),
) -> SystemStatsResponse:
    """
    Get system-wide statistics.

    Returns statistics about events, users, streams, and storage.

    Args:
        request: FastAPI request
        db: AsyncSession - Database session
        api_key: Admin API key

    Returns:
        SystemStatsResponse - System statistics
    """
    try:
        # Get total events count
        query = select(func.count(EventModel.event_id))
        result = await db.execute(query)
        total_events = result.scalar() or 0

        # Get total users count
        query = select(func.count(UserActivity.user_id))
        result = await db.execute(query)
        total_users = result.scalar() or 0

        # Get events by type
        query = select(
            EventModel.event_type, func.count(EventModel.event_id).label("count")
        ).group_by(EventModel.event_type)
        result = await db.execute(query)
        events_by_type = {row[0]: row[1] for row in result.all()}

        # Get Redis stream stats
        stream_stats = await event_producer.get_stream_stats()

        # Get aggregation counts
        query = select(func.count(AggregationOneMinute.id))
        result = await db.execute(query)
        aggregations_1min_count = result.scalar() or 0

        query = select(func.count(AggregationHourly.id))
        result = await db.execute(query)
        aggregations_hourly_count = result.scalar() or 0

        query = select(func.count(AggregationDaily.id))
        result = await db.execute(query)
        aggregations_daily_count = result.scalar() or 0

        return SystemStatsResponse(
            total_events=total_events,
            total_users=total_users,
            events_by_type=events_by_type,
            streams=stream_stats,
            aggregations_1min_count=aggregations_1min_count,
            aggregations_hourly_count=aggregations_hourly_count,
            aggregations_daily_count=aggregations_daily_count,
        )

    except Exception as e:
        logger.error(f"Failed to get system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.get(
    path="/streams",
    summary="Get stream information",
    description="Get detailed information about Redis Streams",
    status_code=status.HTTP_200_OK,
    response_model=StreamStatsResponse,
)
async def get_streams_info(
    api_key: str = Depends(require_admin),
) -> StreamStatsResponse:
    """
    Get information about all Redis Streams.

    Args:
        api_key: Admin API key

    Returns:
        StreamStatsResponse - Stream information
    """
    try:
        return await event_producer.get_stream_stats()
    except Exception as e:
        logger.error(f"Failed to get stream info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stream info: {str(e)}",
        )
