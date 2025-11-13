"""
Redis client for session management and agent state coordination.
"""

import json
from typing import Any, Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from backend.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client for state management."""
    
    def __init__(self):
        self._client: Optional[Redis] = None
        
    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._client.ping()
            logger.info("redis_connected", url=settings.redis_url)
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
            
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("redis_disconnected")
            
    async def set_session(
        self, 
        session_id: str, 
        data: dict[str, Any], 
        ttl: Optional[int] = None
    ) -> None:
        """
        Store session data in Redis.
        
        Args:
            session_id: Unique session identifier
            data: Session data to store
            ttl: Time-to-live in seconds (default: settings.session_timeout)
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")
            
        ttl = ttl or settings.session_timeout
        key = f"session:{session_id}"
        
        await self._client.setex(
            key,
            ttl,
            json.dumps(data)
        )
        logger.debug("session_stored", session_id=session_id)
        
    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session data or None if not found
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")
            
        key = f"session:{session_id}"
        data = await self._client.get(key)
        
        if data:
            logger.debug("session_retrieved", session_id=session_id)
            return json.loads(data)
        return None
        
    async def delete_session(self, session_id: str) -> None:
        """
        Delete session data from Redis.
        
        Args:
            session_id: Unique session identifier
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")
            
        key = f"session:{session_id}"
        await self._client.delete(key)
        logger.debug("session_deleted", session_id=session_id)
        
    async def publish_agent_event(self, channel: str, event: dict[str, Any]) -> None:
        """
        Publish agent event to Redis pub/sub channel.
        
        Args:
            channel: Channel name
            event: Event data to publish
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")
            
        await self._client.publish(channel, json.dumps(event))
        logger.debug("event_published", channel=channel)

    async def iter_channel(self, channel: str):
        """
        Async generator yielding messages published to a channel.
        """
        if not self._client:
            raise RuntimeError("Redis client not connected")
        pubsub: PubSub = self._client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    yield message.get("data")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


redis_client = RedisClient()

