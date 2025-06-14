"""
ENGRAM Real-time Event Broadcasting
Connects the main backend to the dashboard for live data streaming.

Authors: VMG & Claude (2025)
"""

import asyncio
import json
from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime, timezone

from utils.logger import logger


class EngramBroadcaster:
    """Broadcasts engram events to the Neural Observatory dashboard."""
    
    _instance: Optional['EngramBroadcaster'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.dashboard_url = "http://localhost:8080"
            self.session: Optional[aiohttp.ClientSession] = None
            self.connected = False
            self.event_queue = asyncio.Queue(maxsize=1000)
            self.initialized = True
            logger.info("EngramBroadcaster initialized")
    
    async def connect(self):
        """Connect to the dashboard server."""
        if self.connected:
            return
        
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            async with self.session.get(f"{self.dashboard_url}/health") as resp:
                if resp.status == 200:
                    self.connected = True
                    logger.info("Connected to ENGRAM Neural Observatory")
                    # Start event processor
                    asyncio.create_task(self._process_event_queue())
        except Exception as e:
            logger.warning(f"Dashboard not available: {e}")
            self.connected = False
    
    async def broadcast_engram_created(self, engram: Dict[str, Any]):
        """Broadcast when a new engram is created."""
        event = {
            'type': 'engram:created',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'id': engram['id'],
                'thread_id': engram['thread_id'],
                'relevance_score': engram['relevance_score'],
                'surprise_score': engram['surprise_score'],
                'token_count': engram['token_count'],
                'content': engram['content'][:500],  # Preview only
                'created_at': engram['created_at'],
                'metadata': engram.get('metadata', {}),
                'thread_position': engram.get('message_range', {}).get('count', 0)
            }
        }
        
        await self._queue_event(event)
    
    async def broadcast_engram_accessed(self, engram_id: str, related_engrams: list = None):
        """Broadcast when an engram is accessed for retrieval."""
        event = {
            'type': 'engram:accessed',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'id': engram_id,
                'related_engrams': [
                    {
                        'id': e['id'],
                        'strength': e.get('similarity_score', 0.5)
                    } for e in (related_engrams or [])
                ]
            }
        }
        
        await self._queue_event(event)
    
    async def broadcast_metrics_update(self, thread_id: str, metrics: Dict[str, Any]):
        """Broadcast updated metrics for a thread."""
        event = {
            'type': 'metrics:update',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'thread_id': thread_id,
                **metrics
            }
        }
        
        await self._queue_event(event)
    
    async def _queue_event(self, event: Dict[str, Any]):
        """Queue event for broadcasting."""
        if not self.connected:
            await self.connect()
        
        try:
            await self.event_queue.put(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping oldest event")
            try:
                self.event_queue.get_nowait()
                await self.event_queue.put(event)
            except:
                pass
    
    async def _process_event_queue(self):
        """Process queued events and send to dashboard."""
        while self.connected:
            try:
                event = await self.event_queue.get()
                
                # Send via HTTP POST (Socket.IO would be better but this works)
                async with self.session.post(
                    f"{self.dashboard_url}/api/events",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"Failed to broadcast event: {resp.status}")
                
            except Exception as e:
                logger.error(f"Error broadcasting event: {e}")
                await asyncio.sleep(1)
    
    async def close(self):
        """Close the broadcaster connection."""
        self.connected = False
        if self.session:
            await self.session.close()


# Singleton instance
engram_broadcaster = EngramBroadcaster()


# Convenience functions
async def broadcast_engram_created(engram: Dict[str, Any]):
    """Broadcast engram creation event."""
    await engram_broadcaster.broadcast_engram_created(engram)


async def broadcast_engram_accessed(engram_id: str, related_engrams: list = None):
    """Broadcast engram access event."""
    await engram_broadcaster.broadcast_engram_accessed(engram_id, related_engrams)


async def broadcast_metrics_update(thread_id: str, metrics: Dict[str, Any]):
    """Broadcast metrics update."""
    await engram_broadcaster.broadcast_metrics_update(thread_id, metrics)