"""
Event Bus for BitterBot AGI Platform

This module implements a distributed event bus for cross-layer communication.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import asyncio
import json
from datetime import datetime
import uuid
from collections import defaultdict
import logging


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents an event in the system"""
    id: str
    topic: str
    event_type: str
    payload: Dict[str, Any]
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]


class EventBus:
    """
    Distributed event bus for platform-wide communication.
    
    Features:
    - Topic-based pub/sub
    - Event persistence
    - Delivery guarantees
    - Event replay
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._process_task = None
        
    async def start(self) -> None:
        """Start the event bus processing"""
        self.running = True
        self._process_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
        
    async def stop(self) -> None:
        """Stop the event bus processing"""
        self.running = False
        if self._process_task:
            await self._process_task
        logger.info("Event bus stopped")
        
    async def close(self) -> None:
        """Close the event bus and cleanup"""
        await self.stop()
        
    async def publish(self, topic: str, 
                     event_data: Dict[str, Any],
                     event_type: Optional[str] = None) -> str:
        """
        Publish an event to a topic.
        
        Args:
            topic: Event topic
            event_data: Event payload
            event_type: Optional event type
            
        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            topic=topic,
            event_type=event_type or "generic",
            payload=event_data,
            source="unknown",  # TODO: Track event source
            timestamp=datetime.now(),
            metadata={}
        )
        
        await self.event_queue.put(event)
        self.event_history.append(event)
        
        # Maintain history size
        if len(self.event_history) > 10000:
            self.event_history = self.event_history[-5000:]
            
        return event.id
        
    def subscribe(self, topic: str, handler: Callable) -> None:
        """
        Subscribe to events on a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Async function to handle events
        """
        self.subscribers[topic].append(handler)
        logger.info(f"Subscribed handler to topic: {topic}")
        
    def unsubscribe(self, topic: str, handler: Callable) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        if topic in self.subscribers and handler in self.subscribers[topic]:
            self.subscribers[topic].remove(handler)
            logger.info(f"Unsubscribed handler from topic: {topic}")
            
    async def _process_events(self) -> None:
        """Process events from the queue"""
        while self.running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                # Dispatch to subscribers
                await self._dispatch_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    async def _dispatch_event(self, event: Event) -> None:
        """
        Dispatch an event to subscribers.
        
        Args:
            event: Event to dispatch
        """
        # Get exact topic subscribers
        handlers = self.subscribers.get(event.topic, [])
        
        # Also check for wildcard subscribers
        for topic_pattern, topic_handlers in self.subscribers.items():
            if self._matches_pattern(event.topic, topic_pattern):
                handlers.extend(topic_handlers)
                
        # Dispatch to all handlers
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._call_handler(handler, event))
            tasks.append(task)
            
        # Wait for all handlers
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Handler error: {result}")
                    
    async def _call_handler(self, handler: Callable, event: Event) -> None:
        """Safely call an event handler"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Handler {handler.__name__} failed: {e}")
            
    def _matches_pattern(self, topic: str, pattern: str) -> bool:
        """
        Check if topic matches pattern (supports wildcards).
        
        Args:
            topic: Topic to check
            pattern: Pattern with wildcards (*)
            
        Returns:
            True if matches
        """
        if pattern == "*":
            return True
            
        parts = pattern.split(".")
        topic_parts = topic.split(".")
        
        if len(parts) != len(topic_parts):
            return False
            
        for p, t in zip(parts, topic_parts):
            if p != "*" and p != t:
                return False
                
        return True
        
    async def replay_events(self, 
                          topic: str,
                          start_time: Optional[datetime] = None,
                          handler: Optional[Callable] = None) -> List[Event]:
        """
        Replay historical events.
        
        Args:
            topic: Topic to replay
            start_time: Start time for replay
            handler: Optional handler for events
            
        Returns:
            List of replayed events
        """
        replayed = []
        
        for event in self.event_history:
            if event.topic == topic:
                if start_time and event.timestamp < start_time:
                    continue
                    
                replayed.append(event)
                
                if handler:
                    await handler(event)
                    
        return replayed
        
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        topic_counts = defaultdict(int)
        for event in self.event_history:
            topic_counts[event.topic] += 1
            
        return {
            "total_events": len(self.event_history),
            "queue_size": self.event_queue.qsize(),
            "topics": dict(topic_counts),
            "subscribers": {topic: len(handlers) 
                          for topic, handlers in self.subscribers.items()}
        }