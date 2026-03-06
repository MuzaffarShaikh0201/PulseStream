"""
Aggregation worker for computing time-window metrics.
Runs periodically to aggregate events into summary tables.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..db import db_manager
from ..models.database import (
    AggregationDaily,
    AggregationHourly,
    AggregationOneMinute,
    EventModel,
)
from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


class AggregationWorker:
    """
    Worker that computes time-window aggregations.
    Aggregates events into 1-minute, hourly, and daily summaries.
    """

    def __init__(self):
        self.running = False

    async def _aggregate_one_minute(self) -> None:
        """
        Aggregate events into 1-minute windows.
        Processes the last 5 minutes of events.
        """
        async with db_manager.session() as session:
            now = datetime.now(timezone.utc)

            # Round down to the minute
            current_minute = now.replace(second=0, microsecond=0)

            # Process last 5 minutes
            for i in range(5):
                window_start = current_minute - timedelta(minutes=i)
                window_end = window_start + timedelta(minutes=1)

                # Aggregate by event type
                query = (
                    select(
                        EventModel.event_type,
                        func.count(EventModel.event_id).label("event_count"),
                        func.count(func.distinct(EventModel.user_id)).label(
                            "unique_users"
                        ),
                    )
                    .where(
                        and_(
                            EventModel.timestamp >= window_start,
                            EventModel.timestamp < window_end,
                        )
                    )
                    .group_by(EventModel.event_type)
                )

                result = await session.execute(query)
                aggregations = result.all()

                # Upsert aggregations
                for event_type, event_count, unique_users in aggregations:
                    stmt = (
                        pg_insert(AggregationOneMinute)
                        .values(
                            event_type=event_type,
                            window_start=window_start,
                            window_end=window_end,
                            event_count=event_count,
                            unique_users=unique_users,
                            metrics={},
                            created_at=now,
                        )
                        .on_conflict_do_update(
                            index_elements=["event_type", "window_start"],
                            set_={
                                "event_count": event_count,
                                "unique_users": unique_users,
                            },
                        )
                    )

                    await session.execute(stmt)

                if aggregations:
                    logger.debug(
                        f"Aggregated {len(aggregations)} event types for "
                        f"1-min window {window_start}"
                    )

            await session.commit()

    async def _aggregate_hourly(self) -> None:
        """
        Aggregate events into hourly windows.
        Processes the last 24 hours.
        """
        async with db_manager.session() as session:
            now = datetime.now(timezone.utc)

            # Round down to the hour
            current_hour = now.replace(minute=0, second=0, microsecond=0)

            # Process last 24 hours
            for i in range(24):
                hour = current_hour - timedelta(hours=i)
                hour_end = hour + timedelta(hours=1)

                # Aggregate by event type
                query = (
                    select(
                        EventModel.event_type,
                        func.count(EventModel.event_id).label("event_count"),
                        func.count(func.distinct(EventModel.user_id)).label(
                            "unique_users"
                        ),
                    )
                    .where(
                        and_(
                            EventModel.timestamp >= hour,
                            EventModel.timestamp < hour_end,
                        )
                    )
                    .group_by(EventModel.event_type)
                )

                result = await session.execute(query)
                aggregations = result.all()

                # Upsert aggregations
                for event_type, event_count, unique_users in aggregations:
                    stmt = (
                        pg_insert(AggregationHourly)
                        .values(
                            event_type=event_type,
                            hour=hour,
                            event_count=event_count,
                            unique_users=unique_users,
                            avg_processing_time_ms=None,
                            metrics={},
                            created_at=now,
                        )
                        .on_conflict_do_update(
                            index_elements=["event_type", "hour"],
                            set_={
                                "event_count": event_count,
                                "unique_users": unique_users,
                            },
                        )
                    )

                    await session.execute(stmt)

                if aggregations:
                    logger.debug(
                        f"Aggregated {len(aggregations)} event types for "
                        f"hourly window {hour}"
                    )

            await session.commit()

    async def _aggregate_daily(self) -> None:
        """
        Aggregate events into daily windows.
        Processes the last 30 days.
        """
        async with db_manager.session() as session:
            now = datetime.now(timezone.utc)

            # Round down to the day
            current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Process last 30 days
            for i in range(30):
                day = current_day - timedelta(days=i)
                day_end = day + timedelta(days=1)

                # Aggregate by event type
                query = (
                    select(
                        EventModel.event_type,
                        func.count(EventModel.event_id).label("event_count"),
                        func.count(func.distinct(EventModel.user_id)).label(
                            "unique_users"
                        ),
                    )
                    .where(
                        and_(
                            EventModel.timestamp >= day, EventModel.timestamp < day_end
                        )
                    )
                    .group_by(EventModel.event_type)
                )

                result = await session.execute(query)
                aggregations = result.all()

                # Upsert aggregations
                for event_type, event_count, unique_users in aggregations:
                    stmt = (
                        pg_insert(AggregationDaily)
                        .values(
                            event_type=event_type,
                            date=day,
                            event_count=event_count,
                            unique_users=unique_users,
                            metrics={},
                            created_at=now,
                        )
                        .on_conflict_do_update(
                            index_elements=["event_type", "date"],
                            set_={
                                "event_count": event_count,
                                "unique_users": unique_users,
                            },
                        )
                    )

                    await session.execute(stmt)

                if aggregations:
                    logger.debug(
                        f"Aggregated {len(aggregations)} event types for "
                        f"daily window {day.date()}"
                    )

            await session.commit()

    async def run_aggregations(self) -> None:
        """Run all aggregation tasks."""
        logger.info("Running aggregations...")

        try:
            # Run 1-minute aggregations
            await self._aggregate_one_minute()
            logger.info("✓ 1-minute aggregations complete")

            # Run hourly aggregations (every hour)
            await self._aggregate_hourly()
            logger.info("✓ Hourly aggregations complete")

            # Run daily aggregations (once per day would be better, but for demo...)
            await self._aggregate_daily()
            logger.info("✓ Daily aggregations complete")

        except Exception as e:
            logger.error(f"Error running aggregations: {e}", exc_info=True)

    async def start(self) -> None:
        """Start the aggregation worker loop."""
        logger.info("Starting aggregation worker...")

        db_manager.init()
        self.running = True

        while self.running:
            try:
                await self.run_aggregations()

                # Run every minute
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                logger.info("Aggregation worker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}", exc_info=True)
                await asyncio.sleep(60)

        await db_manager.close()
        logger.info("✓ Aggregation worker stopped")

    async def stop(self) -> None:
        """Stop the aggregation worker."""
        self.running = False


async def main():
    """Main entry point for aggregation worker."""
    setup_logging()

    worker = AggregationWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await worker.stop()
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
