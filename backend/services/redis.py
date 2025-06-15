import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from utils.logger import logger
from typing import List, Any

# Redis client
client = None
_initialized = False
_init_lock = asyncio.Lock()

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism


def initialize():
    """Initialize Redis connection using environment variables."""
    global client

    # Load environment variables if not already loaded
    load_dotenv()

    # Get Redis configuration
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', '')
    # Convert string 'True'/'False' to boolean
    redis_ssl_str = os.getenv('REDIS_SSL', 'False')
    redis_ssl = redis_ssl_str.lower() == 'true'

    logger.info(f"Initializing Redis connection to {redis_host}:{redis_port}")

    # Create Redis client with basic configuration
    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        ssl=redis_ssl,
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        retry_on_timeout=True,
        health_check_interval=30
    )

    return client


async def initialize_async():
    """Initialize Redis connection asynchronously."""
    global client, _initialized

    async with _init_lock:
        if not _initialized:
            logger.info("Initializing Redis connection")
            initialize()

            try:
                await client.ping()
                logger.info("Successfully connected to Redis")
                _initialized = True
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                client = None
                raise

    return client


async def close():
    """Close Redis connection."""
    global client, _initialized
    if client:
        logger.info("Closing Redis connection")
        await client.aclose()
        client = None
        _initialized = False
        logger.info("Redis connection closed")


async def get_client():
    """Get the Redis client, initializing if necessary."""
    global client, _initialized
    if client is None or not _initialized:
        await initialize_async()
    return client


# Basic Redis operations
async def set(key: str, value: str, ex: int = None):
    """Set a Redis key."""
    redis_client = await get_client()
    return await redis_client.set(key, value, ex=ex)


async def get(key: str, default: str = None):
    """Get a Redis key."""
    redis_client = await get_client()
    result = await redis_client.get(key)
    return result if result is not None else default


async def delete(key: str):
    """Delete a Redis key."""
    redis_client = await get_client()
    return await redis_client.delete(key)


async def publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    redis_client = await get_client()
    return await redis_client.publish(channel, message)


async def create_pubsub():
    """Create a Redis pubsub object."""
    redis_client = await get_client()
    return redis_client.pubsub()


# List operations
async def rpush(key: str, *values: Any):
    """Append one or more values to a list."""
    redis_client = await get_client()
    return await redis_client.rpush(key, *values)


async def lrange(key: str, start: int, end: int) -> List[str]:
    """Get a range of elements from a list."""
    redis_client = await get_client()
    return await redis_client.lrange(key, start, end)


async def llen(key: str) -> int:
    """Get the length of a list."""
    redis_client = await get_client()
    return await redis_client.llen(key)


# Key management
async def expire(key: str, time: int):
    """Set a key's time to live in seconds."""
    redis_client = await get_client()
    return await redis_client.expire(key, time)


async def keys(pattern: str) -> List[str]:
    """Get keys matching a pattern."""
    redis_client = await get_client()
    return await redis_client.keys(pattern)


class RedisClient:
    """Wrapper class for Redis operations to provide a consistent interface."""
    
    def __init__(self):
        """Initialize the Redis client wrapper."""
        self._client = None
    
    async def _ensure_client(self):
        """Ensure we have a Redis client."""
        if self._client is None:
            self._client = await get_client()
        return self._client
    
    async def get(self, key: str) -> str:
        """Get a value from Redis."""
        client = await self._ensure_client()
        return await client.get(key)
    
    async def set(self, key: str, value: str, ex: int = None) -> bool:
        """Set a value in Redis with optional expiration."""
        client = await self._ensure_client()
        return await client.set(key, value, ex=ex)
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        client = await self._ensure_client()
        return await client.delete(*keys)
    
    async def scan_iter(self, match: str = None, count: int = 100):
        """Scan keys matching a pattern."""
        client = await self._ensure_client()
        cursor = 0
        keys = []
        
        # Use scan to get keys matching pattern
        while True:
            cursor, batch_keys = await client.scan(cursor, match=match, count=count)
            keys.extend(batch_keys)
            
            if cursor == 0:
                break
        
        return keys


# Global Redis client instance for tool cache
_redis_client_instance = None


def get_redis_client() -> RedisClient:
    """Get or create the global Redis client instance for tool cache.
    
    Returns:
        The global RedisClient instance
    """
    global _redis_client_instance
    
    if _redis_client_instance is None:
        _redis_client_instance = RedisClient()
    
    return _redis_client_instance