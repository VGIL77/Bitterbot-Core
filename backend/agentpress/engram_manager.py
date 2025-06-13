"""
Engram-based Memory Consolidation System for AgentPress.

This module implements a neuroscience-inspired memory consolidation system that creates
"engrams" (memory chunks) continuously during conversations, tracks their usage patterns,
and manages their relevance over time.

Based on BitterBot Memory Research concepts:
- Continuous micro-consolidations instead of single large summaries
- Usage-based strengthening (synaptic plasticity analog)
- Dynamic relevance weighting based on access patterns
- Surprise/saliency-based memory gating
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from collections import defaultdict

from litellm import token_counter
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from utils.logger import logger

# Constants for engram management
ENGRAM_CHUNK_SIZE = 5000  # Create engram every 5k tokens (more frequent than 10k for real-time needs)
ENGRAM_SUMMARY_TARGET = 500  # Target tokens for each engram summary
MIN_MESSAGES_FOR_ENGRAM = 3  # Minimum messages to create an engram
SURPRISE_THRESHOLD = 0.3  # Confidence threshold for surprise detection
DECAY_RATE = 0.95  # Daily decay rate for relevance scores
MAX_ENGRAMS_IN_CONTEXT = 5  # Maximum engrams to include in context


class Engram:
    """Represents a single memory engram (consolidation unit)."""
    
    def __init__(self, engram_id: str, thread_id: str, content: str, 
                 metadata: Dict[str, Any], created_at: datetime):
        self.id = engram_id
        self.thread_id = thread_id
        self.content = content  # Summarized content
        self.metadata = metadata
        self.created_at = created_at
        self.access_count = 0
        self.last_accessed = created_at
        self.relevance_score = 1.0
        self.surprise_score = metadata.get('surprise_score', 0.5)
        self.token_count = metadata.get('token_count', 0)
        self.message_range = metadata.get('message_range', {})  # Start/end message IDs
        
    def access(self):
        """Record an access to this engram."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)
        # Boost relevance on access (reinforcement)
        self.relevance_score = min(self.relevance_score * 1.1, 10.0)
        
    def decay(self):
        """Apply time-based decay to relevance score."""
        days_since_access = (datetime.now(timezone.utc) - self.last_accessed).days
        self.relevance_score *= (DECAY_RATE ** days_since_access)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert engram to dictionary for storage."""
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat(),
            'relevance_score': self.relevance_score,
            'surprise_score': self.surprise_score,
            'token_count': self.token_count,
            'message_range': self.message_range
        }


class EngramManager:
    """Manages creation, retrieval, and evolution of memory engrams."""
    
    def __init__(self, chunk_size: int = ENGRAM_CHUNK_SIZE):
        """Initialize the EngramManager.
        
        Args:
            chunk_size: Token count threshold for creating new engrams
        """
        self.db = DBConnection()
        self.chunk_size = chunk_size
        self.active_buffers: Dict[str, List[Dict]] = {}  # thread_id -> messages buffer
        self.token_counts: Dict[str, int] = {}  # thread_id -> current token count
        
    async def process_message(self, thread_id: str, message: Dict[str, Any], 
                            force_consolidation: bool = False) -> Optional[Engram]:
        """Process a new message and potentially create an engram.
        
        Args:
            thread_id: The thread ID
            message: The message to process
            force_consolidation: Force creation of engram regardless of token count
            
        Returns:
            Created engram if consolidation occurred, None otherwise
        """
        # Initialize buffer if needed
        if thread_id not in self.active_buffers:
            self.active_buffers[thread_id] = []
            self.token_counts[thread_id] = 0
            
        # Add message to buffer
        self.active_buffers[thread_id].append(message)
        
        # Count tokens in the message
        message_tokens = await self._count_message_tokens(message)
        self.token_counts[thread_id] += message_tokens
        
        # Check if we should consolidate
        should_consolidate = (
            force_consolidation or 
            self.token_counts[thread_id] >= self.chunk_size or
            (len(self.active_buffers[thread_id]) >= MIN_MESSAGES_FOR_ENGRAM and
             await self._detect_surprise(message))
        )
        
        if should_consolidate:
            engram = await self._create_engram(thread_id)
            # Reset buffer and counter
            self.active_buffers[thread_id] = []
            self.token_counts[thread_id] = 0
            return engram
            
        return None
        
    async def _create_engram(self, thread_id: str) -> Optional[Engram]:
        """Create an engram from the current buffer."""
        messages = self.active_buffers.get(thread_id, [])
        if len(messages) < MIN_MESSAGES_FOR_ENGRAM:
            logger.debug(f"Not enough messages for engram in thread {thread_id}")
            return None
            
        try:
            # Generate summary
            summary = await self._generate_summary(messages)
            
            # Calculate metadata
            metadata = {
                'message_count': len(messages),
                'token_count': self.token_counts.get(thread_id, 0),
                'topics': await self._extract_topics(messages),
                'surprise_score': await self._calculate_surprise_score(messages),
                'message_range': {
                    'start': messages[0].get('id'),
                    'end': messages[-1].get('id')
                }
            }
            
            # Create engram
            engram_id = str(uuid.uuid4())
            engram = Engram(
                engram_id=engram_id,
                thread_id=thread_id,
                content=summary,
                metadata=metadata,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store in database
            await self._store_engram(engram)
            
            logger.info(f"Created engram {engram_id} for thread {thread_id} with {len(messages)} messages")
            return engram
            
        except Exception as e:
            logger.error(f"Error creating engram for thread {thread_id}: {e}")
            return None
            
    async def retrieve_relevant_engrams(self, thread_id: str, query: str, 
                                      limit: int = MAX_ENGRAMS_IN_CONTEXT) -> List[Engram]:
        """Retrieve most relevant engrams for a query.
        
        Uses a combination of:
        - Semantic similarity (if vector store available)
        - Recency
        - Relevance score (access patterns)
        - Topic matching
        """
        try:
            client = await self.db.client
            
            # For now, use a simple query - in production, use vector similarity
            result = await client.table('engrams').select('*').eq(
                'thread_id', thread_id
            ).order('relevance_score', desc=True).limit(limit * 2).execute()
            
            if not result.data:
                return []
                
            # Convert to Engram objects and apply decay
            engrams = []
            for data in result.data:
                engram = self._engram_from_dict(data)
                engram.decay()  # Apply time-based decay
                engrams.append(engram)
                
            # Sort by combined score (relevance * recency factor)
            engrams.sort(key=lambda e: e.relevance_score, reverse=True)
            
            # Return top N
            selected = engrams[:limit]
            
            # Record access for selected engrams
            for engram in selected:
                engram.access()
                await self._update_engram_access(engram)
                
            return selected
            
        except Exception as e:
            logger.error(f"Error retrieving engrams: {e}")
            return []
            
    async def get_thread_engram_summary(self, thread_id: str) -> str:
        """Get a high-level summary of all engrams for a thread."""
        engrams = await self.retrieve_relevant_engrams(thread_id, "", limit=20)
        
        if not engrams:
            return "No memory consolidations available for this conversation."
            
        summary_parts = [
            f"Memory consolidations from this conversation ({len(engrams)} engrams):",
            ""
        ]
        
        for i, engram in enumerate(engrams[:10], 1):  # Show top 10
            summary_parts.append(f"{i}. {engram.content[:100]}...")
            
        return "\n".join(summary_parts)
        
    async def _generate_summary(self, messages: List[Dict]) -> str:
        """Generate a concise summary of messages."""
        # Format messages for summarization
        formatted_messages = []
        for msg in messages:
            role = msg.get('type', 'unknown')
            content = json.loads(msg.get('content', '{}')).get('content', '')
            formatted_messages.append(f"{role.upper()}: {content}")
            
        conversation_text = "\n".join(formatted_messages)
        
        system_prompt = """You are a memory consolidation system inspired by neuroscience.
Your task is to create a concise "engram" (memory consolidation) from a conversation segment.

Focus on:
1. Key decisions, conclusions, or insights
2. Important facts or information exchanged
3. Problems solved or questions answered
4. Emotional significance or surprising elements
5. Action items or future references

Be extremely concise (aim for 2-3 sentences max) but preserve essential information.
Write in a way that would help someone quickly understand what happened in this conversation segment."""
        
        try:
            response = await make_llm_api_call(
                model_name="openai/gpt-4o-mini",  # Fast, cheap model for summaries
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create an engram from:\n\n{conversation_text}"}
                ],
                temperature=0.3,
                max_tokens=ENGRAM_SUMMARY_TARGET
            )
            
            if response and hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "Failed to generate summary"
                
        except Exception as e:
            logger.error(f"Error generating engram summary: {e}")
            return "Error creating memory consolidation"
            
    async def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract main topics from messages."""
        # Simple implementation - in production, use NLP/embedding clustering
        topics = set()
        
        for msg in messages:
            content = json.loads(msg.get('content', '{}')).get('content', '').lower()
            # Look for common topic indicators
            if 'code' in content or 'programming' in content:
                topics.add('coding')
            if 'error' in content or 'bug' in content:
                topics.add('debugging')
            if 'design' in content or 'ui' in content:
                topics.add('design')
            # Add more topic detection as needed
            
        return list(topics)
        
    async def _calculate_surprise_score(self, messages: List[Dict]) -> float:
        """Calculate surprise score based on message patterns."""
        # Placeholder - in production, use model confidence scores
        # High surprise = unexpected content, errors, new topics
        
        surprise_indicators = ['error', 'unexpected', 'strange', 'wow', 'interesting', 'oh', '!']
        surprise_count = 0
        
        for msg in messages:
            content = json.loads(msg.get('content', '{}')).get('content', '').lower()
            for indicator in surprise_indicators:
                if indicator in content:
                    surprise_count += 1
                    
        # Normalize to 0-1 range
        return min(surprise_count / (len(messages) * 2), 1.0)
        
    async def _detect_surprise(self, message: Dict) -> bool:
        """Detect if a message represents surprising/important information."""
        content = json.loads(message.get('content', '{}')).get('content', '').lower()
        
        # Simple heuristic - in production, use model uncertainty
        surprise_indicators = ['error', 'failed', 'unexpected', 'never seen', 'strange']
        
        return any(indicator in content for indicator in surprise_indicators)
        
    async def _count_message_tokens(self, message: Dict) -> int:
        """Count tokens in a message."""
        content = json.loads(message.get('content', '{}')).get('content', '')
        # Use litellm token counter
        return token_counter(model="gpt-4", messages=[{"role": "user", "content": content}])
        
    async def _store_engram(self, engram: Engram):
        """Store engram in database."""
        client = await self.db.client
        
        await client.table('engrams').insert(engram.to_dict()).execute()
        
    async def _update_engram_access(self, engram: Engram):
        """Update engram access statistics in database."""
        client = await self.db.client
        
        await client.table('engrams').update({
            'access_count': engram.access_count,
            'last_accessed': engram.last_accessed.isoformat(),
            'relevance_score': engram.relevance_score
        }).eq('id', engram.id).execute()
        
    def _engram_from_dict(self, data: Dict) -> Engram:
        """Create Engram object from database record."""
        engram = Engram(
            engram_id=data['id'],
            thread_id=data['thread_id'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at'])
        )
        engram.access_count = data.get('access_count', 0)
        engram.last_accessed = datetime.fromisoformat(data.get('last_accessed', data['created_at']))
        engram.relevance_score = data.get('relevance_score', 1.0)
        engram.surprise_score = data.get('surprise_score', 0.5)
        engram.token_count = data.get('token_count', 0)
        engram.message_range = data.get('message_range', {})
        
        return engram
        
    async def cleanup_old_engrams(self, days_threshold: int = 30, 
                                relevance_threshold: float = 0.1):
        """Clean up old, low-relevance engrams."""
        try:
            client = await self.db.client
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
            
            # Delete engrams that are both old and low relevance
            result = await client.table('engrams').delete().lt(
                'relevance_score', relevance_threshold
            ).lt('last_accessed', cutoff_date.isoformat()).execute()
            
            if result.data:
                logger.info(f"Cleaned up {len(result.data)} old engrams")
                
        except Exception as e:
            logger.error(f"Error cleaning up engrams: {e}")