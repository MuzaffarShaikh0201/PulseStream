"""
Redis connection and client management.
Handles Redis Streams operations for event processing.
"""

from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from ..config import settings


class RedisManager:
    """Redis connection manager for event streaming."""

    def __init__(self):
        self._client: Optional[Redis] = None

    async def init(self) -> None:
        """Initialize Redis connection pool."""
        self._client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_pool_size,
        )

        # Initialize consumer groups for all streams
        await self._init_consumer_groups()

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.aclose()

    async def _init_consumer_groups(self) -> None:
        """
        Initialize consumer groups for all event streams.
        Creates streams and consumer groups if they don't exist.
        """
        streams = [
            settings.redis_stream_user_events,
            settings.redis_stream_activity_events,
            settings.redis_stream_transaction_events,
            settings.redis_stream_system_events,
        ]

        for stream_key in streams:
            try:
                # Try to create consumer group
                # MKSTREAM creates the stream if it doesn't exist
                await self._client.xgroup_create(
                    name=stream_key,
                    groupname=settings.redis_consumer_group,
                    id="0",
                    mkstream=True,
                )
            except RedisError as e:
                # Group already exists, which is fine
                if "BUSYGROUP" not in str(e):
                    raise

    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("RedisManager not initialized. Call init() first.")
        return self._client

    async def ping(self) -> bool:
        """
        Ping Redis to check connection.

        Returns:
            True if connected, False otherwise
        """
        try:
            return await self.client.ping()
        except RedisError:
            return False

    async def xadd(
        self,
        stream_key: str,
        data: Dict[str, Any],
        maxlen: Optional[int] = None,
        approximate: bool = True,
    ) -> str:
        """
        Add entry to Redis Stream.

        Args:
            stream_key: Stream name
            data: Dictionary of field-value pairs
            maxlen: Maximum stream length (for trimming)
            approximate: Use approximate trimming (~)

        Returns:
            Entry ID
        """
        return await self.client.xadd(
            name=stream_key,
            fields=data,
            maxlen=maxlen or settings.redis_stream_maxlen,
            approximate=approximate,
        )

    async def xread(
        self,
        streams: Dict[str, str],
        count: Optional[int] = None,
        block: Optional[int] = None,
    ) -> List:
        """
        Read from Redis Streams.

        Args:
            streams: Dictionary of stream_name: last_id
            count: Maximum number of entries to return
            block: Block for N milliseconds (None = non-blocking)

        Returns:
            List of stream entries
        """
        return await self.client.xread(
            streams=streams, count=count or settings.redis_batch_size, block=block
        )

    async def xreadgroup(
        self,
        groupname: str,
        consumername: str,
        streams: Dict[str, str],
        count: Optional[int] = None,
        block: Optional[int] = None,
        noack: bool = False,
    ) -> List:
        """
        Read from Redis Streams as part of a consumer group.

        Args:
            groupname: Consumer group name
            consumername: Consumer name
            streams: Dictionary of stream_name: last_id (use '>' for new messages)
            count: Maximum number of entries to return
            block: Block for N milliseconds
            noack: Don't require acknowledgment

        Returns:
            List of stream entries
        """
        return await self.client.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams=streams,
            count=count or settings.redis_batch_size,
            block=block,
            noack=noack,
        )

    async def xack(self, stream_key: str, groupname: str, *ids: str) -> int:
        """
        Acknowledge processing of stream entries.

        Args:
            stream_key: Stream name
            groupname: Consumer group name
            ids: Entry IDs to acknowledge

        Returns:
            Number of entries acknowledged
        """
        return await self.client.xack(stream_key, groupname, *ids)

    async def xlen(self, stream_key: str) -> int:
        """
        Get the length of a stream.

        Args:
            stream_key: Stream name

        Returns:
            Number of entries in stream
        """
        return await self.client.xlen(stream_key)

    async def get_stream_info(self, stream_key: str) -> Dict[str, Any]:
        """
        Get information about a stream.

        Args:
            stream_key: Stream name

        Returns:
            Stream information
        """
        return await self.client.xinfo_stream(stream_key)

    async def get_consumer_group_info(
        self, stream_key: str, groupname: str
    ) -> List[Dict[str, Any]]:
        """
        Get information about consumers in a group.

        Args:
            stream_key: Stream name
            groupname: Consumer group name

        Returns:
            List of consumer information
        """
        return await self.client.xinfo_consumers(stream_key, groupname)


# Global Redis manager instance
redis_manager = RedisManager()
