"""
Tool Result Caching System.

This module provides caching functionality for tool execution results,
reducing API costs and improving response times for repeated operations.
"""

import hashlib
import json
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable, Union
from datetime import datetime, timedelta

from services.redis import RedisClient
from utils.logger import logger


class ToolCache:
    """Manages caching for tool execution results."""
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize the ToolCache.
        
        Args:
            redis_client: Optional Redis client instance. If not provided,
                         caching will be disabled gracefully.
        """
        self.redis = redis_client
        self._cache_enabled = redis_client is not None
        self._stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
        
        if not self._cache_enabled:
            logger.warning("Tool caching disabled - Redis client not available")
    
    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key for tool execution.
        
        Args:
            tool_name: Name of the tool being executed
            params: Parameters passed to the tool
            
        Returns:
            A unique cache key string
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        content = f"{tool_name}:{sorted_params}"
        
        # Create hash for more efficient storage
        hash_object = hashlib.sha256(content.encode())
        return f"tool_cache:{tool_name}:{hash_object.hexdigest()}"
    
    async def get(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve cached result for tool execution.
        
        Args:
            tool_name: Name of the tool
            params: Parameters passed to the tool
            
        Returns:
            Cached result if available, None otherwise
        """
        if not self._cache_enabled:
            return None
            
        try:
            cache_key = self._generate_cache_key(tool_name, params)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                self._stats['hits'] += 1
                logger.debug(f"Cache hit for {tool_name} with key {cache_key}")
                return json.loads(cached_data)
            else:
                self._stats['misses'] += 1
                return None
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    async def set(
        self, 
        tool_name: str, 
        params: Dict[str, Any], 
        result: Any, 
        ttl: int = 300
    ) -> bool:
        """Cache tool execution result.
        
        Args:
            tool_name: Name of the tool
            params: Parameters passed to the tool
            result: Result to cache
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._cache_enabled:
            return False
            
        try:
            cache_key = self._generate_cache_key(tool_name, params)
            cache_data = {
                'result': result,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
            
            await self.redis.set(
                cache_key, 
                json.dumps(cache_data),
                ex=ttl
            )
            
            logger.debug(f"Cached result for {tool_name} with key {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def invalidate(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Invalidate cached results.
        
        Args:
            tool_name: Name of the tool
            params: Optional specific parameters to invalidate.
                   If None, invalidates all cache for the tool.
                   
        Returns:
            True if invalidation successful
        """
        if not self._cache_enabled:
            return False
            
        try:
            if params:
                # Invalidate specific cache entry
                cache_key = self._generate_cache_key(tool_name, params)
                await self.redis.delete(cache_key)
                logger.info(f"Invalidated cache for {tool_name} with specific params")
            else:
                # Invalidate all entries for this tool
                # Note: This requires scanning keys which can be expensive
                pattern = f"tool_cache:{tool_name}:*"
                keys = await self.redis.scan_iter(match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"Invalidated all cache entries for {tool_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total if total > 0 else 0
        
        return {
            'enabled': self._cache_enabled,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'errors': self._stats['errors'],
            'hit_rate': round(hit_rate * 100, 2),
            'total_requests': total
        }


def cache_tool_result(
    ttl: Union[int, Callable] = 300,
    cache_condition: Optional[Callable] = None,
    key_params: Optional[list] = None
):
    """Decorator to cache tool execution results.
    
    Args:
        ttl: Time to live in seconds or callable that returns TTL
        cache_condition: Optional function to determine if result should be cached
        key_params: Optional list of parameter names to use for cache key
                   (if not provided, all params are used)
    
    Example:
        @cache_tool_result(ttl=600)
        async def execute(self, query: str):
            return await expensive_api_call(query)
            
        @cache_tool_result(
            ttl=lambda result: 3600 if result['status'] == 'success' else 60,
            cache_condition=lambda result: result is not None
        )
        async def execute(self, params):
            return await api_call(params)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if tool has caching enabled
            if not hasattr(self, '_cache') or not self._cache:
                return await func(self, *args, **kwargs)
            
            # Extract parameters for cache key
            if key_params:
                cache_params = {k: kwargs.get(k) for k in key_params if k in kwargs}
            else:
                cache_params = kwargs
            
            # Try to get from cache
            tool_name = self.__class__.__name__
            cached_result = await self._cache.get(tool_name, cache_params)
            
            if cached_result:
                logger.info(f"Returning cached result for {tool_name}")
                return cached_result['result']
            
            # Execute the tool
            start_time = time.time()
            result = await func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Determine if we should cache the result
            should_cache = True
            if cache_condition:
                should_cache = cache_condition(result)
            
            if should_cache:
                # Calculate TTL
                cache_ttl = ttl
                if callable(ttl):
                    cache_ttl = ttl(result)
                
                # Cache the result
                await self._cache.set(tool_name, cache_params, result, cache_ttl)
                logger.info(f"Cached {tool_name} result (execution: {execution_time:.2f}s, TTL: {cache_ttl}s)")
            
            return result
            
        return wrapper
    return decorator


# Global cache instance
_tool_cache_instance = None

def get_tool_cache() -> ToolCache:
    """Get or create the global tool cache instance.
    
    Returns:
        The global ToolCache instance
    """
    global _tool_cache_instance
    
    if _tool_cache_instance is None:
        try:
            from services.redis import get_redis_client
            redis_client = get_redis_client()
            _tool_cache_instance = ToolCache(redis_client)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for tool cache: {e}")
            _tool_cache_instance = ToolCache(None)
    
    return _tool_cache_instance