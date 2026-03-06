"""
Base consumer worker for processing events from Redis Streams.
"""

import json
import signal
import asyncio
from uuid import UUID
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import db_manager, redis_manager
from ..models.database import EventModel, UserActivity
from ..utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


class EventConsumerWorker:
    """
    Consumer worker that processes events from Redis Streams.
    Reads events, processes them, and writes to PostgreSQL.
    """

    def __init__(self, consumer_name: Optional[str] = None):
        """
        Initialize consumer worker.

        Args:
            consumer_name: Unique name for this consumer (defaults to hostname-pid)
        """
        import socket
        import os

        self.consumer_name = consumer_name or f"{socket.gethostname()}-{os.getpid()}"
        self.running = False
        self.processed_count = 0
        self.error_count = 0

        # Streams to consume from
        self.streams = {
            settings.redis_stream_user_events: ">",
            settings.redis_stream_activity_events: ">",
            settings.redis_stream_transaction_events: ">",
            settings.redis_stream_system_events: ">",
        }

    def _deserialize_event(self, event_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Deserialize event from Redis Stream format.

        Args:
            event_data: Raw event data from Redis

        Returns:
            Deserialized event dictionary
        """
        return {
            "event_id": UUID(event_data["event_id"]),
            "event_type": event_data["event_type"],
            "user_id": event_data["user_id"] if event_data["user_id"] else None,
            "session_id": (
                event_data["session_id"] if event_data["session_id"] else None
            ),
            "timestamp": datetime.fromisoformat(event_data["timestamp"]),
            "event_metadata": json.loads(event_data["metadata"]),
            "properties": json.loads(event_data["properties"]),
            "created_at": datetime.fromisoformat(event_data["created_at"]),
        }

    async def _process_events_batch(
        self, session: AsyncSession, events: List[Dict[str, Any]]
    ) -> None:
        """
        Process a batch of events and insert into database.

        Args:
            session: Database session
            events: List of deserialized events
        """
        if not events:
            return

        # Bulk insert events
        stmt = insert(EventModel).values(events)
        await session.execute(stmt)

        # Update user activity for events with user_id
        for event in events:
            if event.get("user_id"):
                await self._update_user_activity(session, event)

        await session.commit()
        logger.debug(f"Inserted {len(events)} events into database")

    async def _update_user_activity(
        self, session: AsyncSession, event: Dict[str, Any]
    ) -> None:
        """
        Update user activity summary.

        Args:
            session: Database session
            event: Event data
        """
        from sqlalchemy import select
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        user_id = event["user_id"]
        timestamp = event["timestamp"]
        event_type = event["event_type"]

        # Upsert user activity
        stmt = (
            pg_insert(UserActivity)
            .values(
                user_id=user_id,
                first_seen=timestamp,
                last_seen=timestamp,
                total_events=1,
                last_event_type=event_type,
                activity_data={},
                updated_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "last_seen": timestamp,
                    "total_events": UserActivity.total_events + 1,
                    "last_event_type": event_type,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        )

        await session.execute(stmt)

    async def _consume_stream(self) -> None:
        """
        Main consumer loop - reads from Redis Streams and processes events.
        """
        logger.info(
            f"Consumer {self.consumer_name} started, "
            f"reading from {len(self.streams)} streams"
        )

        consecutive_errors = 0
        max_consecutive_errors = 10

        while self.running:
            try:
                # Read from streams with blocking
                results = await redis_manager.xreadgroup(
                    groupname=settings.redis_consumer_group,
                    consumername=self.consumer_name,
                    streams=self.streams,
                    count=settings.redis_batch_size,
                    block=1000,  # Block for 1 second
                )

                if not results:
                    # No new messages
                    await asyncio.sleep(0.1)
                    continue

                # Process each stream's messages
                for stream_name, messages in results:
                    if not messages:
                        continue

                    # Deserialize events
                    events_to_insert = []
                    message_ids = []

                    for message_id, event_data in messages:
                        try:
                            event = self._deserialize_event(event_data)
                            events_to_insert.append(event)
                            message_ids.append(message_id)
                        except Exception as e:
                            logger.error(
                                f"Failed to deserialize event {message_id}: {e}"
                            )
                            self.error_count += 1

                    # Insert events into database
                    if events_to_insert:
                        try:
                            async with db_manager.session() as session:
                                await self._process_events_batch(
                                    session, events_to_insert
                                )

                            # Acknowledge processed messages
                            await redis_manager.xack(
                                stream_name, settings.redis_consumer_group, *message_ids
                            )

                            self.processed_count += len(events_to_insert)

                            logger.info(
                                f"Processed {len(events_to_insert)} events from {stream_name} "
                                f"(total: {self.processed_count})"
                            )

                            # Reset error counter on success
                            consecutive_errors = 0

                        except Exception as e:
                            logger.error(
                                f"Failed to process batch from {stream_name}: {e}",
                                exc_info=True,
                            )
                            self.error_count += 1
                            consecutive_errors += 1

                            # If too many consecutive errors, pause
                            if consecutive_errors >= max_consecutive_errors:
                                logger.error(
                                    f"Too many consecutive errors ({consecutive_errors}), "
                                    "pausing for 30 seconds..."
                                )
                                await asyncio.sleep(30)
                                consecutive_errors = 0

            except asyncio.CancelledError:
                logger.info("Consumer cancelled, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
                self.error_count += 1
                await asyncio.sleep(5)

    async def start(self) -> None:
        """Start the consumer worker."""
        logger.info(f"Initializing consumer worker: {self.consumer_name}")

        # Initialize connections
        db_manager.init()
        await redis_manager.init()

        logger.info("✓ Database and Redis connections initialized")

        # Start consuming
        self.running = True
        await self._consume_stream()

    async def stop(self) -> None:
        """Stop the consumer worker gracefully."""
        logger.info(f"Stopping consumer worker: {self.consumer_name}")
        self.running = False

        # Close connections
        await redis_manager.close()
        await db_manager.close()

        logger.info(
            f"✓ Consumer stopped. Processed: {self.processed_count}, "
            f"Errors: {self.error_count}"
        )


async def main():
    """Main entry point for the consumer worker."""
    setup_logging()

    worker = EventConsumerWorker()

    # Different signal handling for Windows vs Unix
    import platform

    if platform.system() != "Windows":
        # Unix/Linux signal handling
        loop = asyncio.get_event_loop()

        def signal_handler(sig):
            logger.info(f"Received signal {sig}, initiating graceful shutdown...")
            asyncio.create_task(worker.stop())

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

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
