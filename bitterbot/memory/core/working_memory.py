from typing import Dict, List, Any
from datetime import datetime, timedelta

class WorkingMemory:
    """Short-term memory for current session - Redis-backed"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self.cache = {}  # TODO: Replace with Redis client
        
    async def store(self, key: str, value: Any, user_id: str):
        """Store item in working memory"""
        # TODO: Implement Redis storage with TTL
        self.cache[f"{user_id}:{key}"] = {
            'value': value,
            'timestamp': datetime.now()
        }
        
    async def retrieve(self, key: str, user_id: str):
        """Retrieve from working memory"""
        # TODO: Implement Redis retrieval
        return self.cache.get(f"{user_id}:{key}")
        
    async def get_recent(self, user_id: str, k: int = 5):
        """Get k most recent items"""
        # TODO: Implement time-based retrieval
        return []