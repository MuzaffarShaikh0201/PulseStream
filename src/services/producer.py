"""
Event producer service.
Publishes events to Redis Streams.
"""

import json
from typing import Any, Dict, List

from ..config import settings
from ..db import redis_manager
from ..models import Event
from ..models.admin import StreamStats, StreamStatsResponse
from ..utils.logging import get_logger


logger = get_logger(__name__)


class EventProducer:
    """
    Event producer for publishing events to Redis Streams.
    """

    def __init__(self):
        self.redis = redis_manager

    def _serialize_event(self, event: Event) -> Dict[str, str]:
        """
        Serialize event to string dictionary for Redis.

        Args:
            event: Event object

        Returns:
            Dictionary with string values
        """
        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "user_id": event.user_id or "",
            "session_id": event.session_id or "",
            "timestamp": event.timestamp.isoformat(),
            "metadata": json.dumps(
                event.metadata.model_dump() if event.metadata else {}
            ),
            "properties": json.dumps(event.properties or {}),
            "created_at": event.created_at.isoformat(),
        }

    async def publish_event(self, event: Event) -> str:
        """
        Publish a single event to the appropriate Redis Stream.

        Args:
            event: Event to publish

        Returns:
            Stream entry ID

        Raises:
            RedisError: If publishing fails
        """
        # Get the appropriate stream for this event type
        stream_key = settings.get_stream_key(event.event_type)

        # Serialize event
        event_data = self._serialize_event(event)

        # Publish to Redis Stream
        try:
            entry_id = await self.redis.xadd(
                stream_key=stream_key,
                data=event_data,
                maxlen=settings.redis_stream_maxlen,
                approximate=True,
            )

            logger.debug(
                f"Published event {event.event_id} to stream {stream_key} "
                f"with entry ID {entry_id}"
            )

            return entry_id

        except Exception as e:
            logger.error(
                f"Failed to publish event {event.event_id} to stream {stream_key}: {e}"
            )
            raise

    async def publish_events_batch(self, events: List[Event]) -> List[str]:
        """
        Publish multiple events to Redis Streams.
        Uses pipelining for better performance.

        Args:
            events: List of events to publish

        Returns:
            List of stream entry IDs
        """
        if not events:
            return []

        # Group events by stream
        events_by_stream: Dict[str, List[Event]] = {}
        for event in events:
            stream_key = settings.get_stream_key(event.event_type)
            if stream_key not in events_by_stream:
                events_by_stream[stream_key] = []
            events_by_stream[stream_key].append(event)

        # Use pipeline for batch operations
        entry_ids = []

        try:
            async with self.redis.client.pipeline(transaction=False) as pipe:
                for stream_key, stream_events in events_by_stream.items():
                    for event in stream_events:
                        event_data = self._serialize_event(event)
                        pipe.xadd(
                            name=stream_key,
                            fields=event_data,
                            maxlen=settings.redis_stream_maxlen,
                            approximate=True,
                        )

                # Execute all commands
                results = await pipe.execute()
                entry_ids = [str(r) for r in results]

            logger.info(
                f"Published {len(events)} events across "
                f"{len(events_by_stream)} streams"
            )

            return entry_ids

        except Exception as e:
            logger.error(f"Failed to publish batch of {len(events)} events: {e}")
            raise

    def _extract_entry_id(self, entry: object) -> str | None:
        """Extract entry ID from Redis XINFO first-entry/last-entry format."""
        if entry is None:
            return None
        if isinstance(entry, (list, tuple)) and len(entry) > 0:
            entry_id = entry[0]
            return str(entry_id) if entry_id is not None else None
        return str(entry)

    async def get_stream_stats(self) -> StreamStatsResponse:
        """
        Get statistics for all event streams.

        Returns:
            StreamStatsResponse - Stream statistics
        """
        stream_keys = [
            settings.redis_stream_user_events,
            settings.redis_stream_activity_events,
            settings.redis_stream_transaction_events,
            settings.redis_stream_system_events,
        ]

        streams: List[StreamStats] = []
        total_messages = 0

        for stream_key in stream_keys:
            try:
                length = await self.redis.xlen(stream_key)
                total_messages += length
                info = await self.redis.get_stream_info(stream_key)

                first_entry = info.get("first-entry")
                last_entry = info.get("last-entry")
                groups = info.get("groups", 0)

                streams.append(
                    StreamStats(
                        stream_key=stream_key,
                        length=length,
                        first_entry_id=self._extract_entry_id(first_entry),
                        last_entry_id=self._extract_entry_id(last_entry),
                        groups=groups,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to get stats for stream {stream_key}: {e}")
                streams.append(StreamStats(stream_key=stream_key, error=str(e)))

        return StreamStatsResponse(
            total_streams=len(stream_keys),
            total_messages=total_messages,
            total_consumers=0,
            total_pending_messages=0,
            total_backlog=total_messages,
            streams=streams,
        )


# Global producer instance
event_producer = EventProducer()
