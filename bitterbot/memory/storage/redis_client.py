import redis
import json
from typing import Any, Optional
from datetime import timedelta

class RedisClient:
    """Redis client wrapper for caching"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        # TODO: Configure Redis connection
        try:
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()
        except:
            # Fallback to in-memory dict if Redis not available
            self.client = None
            self.memory_cache = {}
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value with optional TTL"""
        if self.client:
            # TODO: Implement async Redis set
            value_str = json.dumps(value) if not isinstance(value, str) else value
            if ttl:
                self.client.setex(key, ttl, value_str)
            else:
                self.client.set(key, value_str)
        else:
            # Fallback to memory cache
            self.memory_cache[key] = value
            
    async def get(self, key: str) -> Optional[Any]:
        """Get a value"""
        if self.client:
            # TODO: Implement async Redis get
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
        else:
            return self.memory_cache.get(key)
            
    async def delete(self, key: str):
        """Delete a key"""
        if self.client:
            self.client.delete(key)
        else:
            self.memory_cache.pop(key, None)
            
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.client:
            return bool(self.client.exists(key))
        else:
            return key in self.memory_cache