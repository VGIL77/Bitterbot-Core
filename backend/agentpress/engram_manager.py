"""
Engram Memory Management System.

A neuroscience-inspired continuous memory consolidation system that creates
"engrams" (memory chunks) throughout conversations to prevent context window
overflow and maintain long-term conversational coherence.

Created in collaboration between Victor Michael Gil and Claude.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from collections import defaultdict
import numpy as np

from services.supabase import DBConnection
from services.llm import make_llm_api_call
from utils.logger import logger
from .engram_metrics import log_engram_created, log_engram_retrieved

# Configuration constants
ENGRAM_CHUNK_SIZE = 5000  # Create engram every 5k tokens
DECAY_RATE = 0.95  # Daily decay rate for relevance scores
MAX_ENGRAMS_IN_CONTEXT = 5  # Maximum engrams to include in context
SURPRISE_THRESHOLD = 0.7  # Threshold for surprise-triggered consolidation
MIN_MESSAGES_FOR_ENGRAM = 3  # Minimum messages to create an engram
RELEVANCE_BOOST_ON_ACCESS = 0.2  # Boost to relevance when accessed


class EngramManager:
    """
    Manages the creation, storage, and retrieval of memory engrams.
    
    This system is inspired by how the human brain consolidates memories,
    creating compressed representations of experience that can be efficiently
    retrieved when needed.
    """
    
    def __init__(self):
        self.db = DBConnection()
        self._consolidation_locks = {}  # Prevent concurrent consolidations
        
    async def create_engram(
        self,
        thread_id: str,
        messages: List[Dict[str, Any]],
        trigger: str = "token_threshold",
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new engram from a sequence of messages.
        
        Args:
            thread_id: Thread to create engram for
            messages: Messages to consolidate
            trigger: What triggered creation ("token_threshold", "surprise", "forced")
            force: Force creation even if below thresholds
            
        Returns:
            Created engram or None if creation failed/skipped
        """
        # Prevent concurrent consolidations for the same thread
        if thread_id in self._consolidation_locks:
            logger.warning(f"Consolidation already in progress for thread {thread_id}")
            return None
            
        self._consolidation_locks[thread_id] = True
        
        try:
            # Validate we have enough messages
            if len(messages) < MIN_MESSAGES_FOR_ENGRAM and not force:
                logger.debug(f"Not enough messages for engram: {len(messages)} < {MIN_MESSAGES_FOR_ENGRAM}")
                return None
                
            # Calculate token count (rough estimate)
            token_count = sum(
                len(json.dumps(msg).split()) * 1.3  # Rough token estimate
                for msg in messages
            )
            
            # Generate consolidated summary
            summary = await self._generate_summary(messages)
            if not summary:
                logger.error("Failed to generate engram summary")
                return None
                
            # Calculate surprise score
            surprise_score = await self._calculate_surprise_score(messages, summary)
            
            # Extract topics
            topics = await self._extract_topics(summary)
            
            # Create engram record
            client = await self.db.client
            
            engram_data = {
                "thread_id": thread_id,
                "content": summary,
                "message_range": {
                    "start": messages[0].get('message_id'),
                    "end": messages[-1].get('message_id'),
                    "count": len(messages)
                },
                "token_count": int(token_count),
                "relevance_score": 1.0,  # Start with full relevance
                "surprise_score": surprise_score,
                "access_count": 0,
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "trigger": trigger,
                    "topics": topics,
                    "message_types": self._count_message_types(messages),
                    "has_code": any("```" in str(msg.get('content', '')) for msg in messages),
                    "has_error": any("error" in str(msg.get('content', '')).lower() for msg in messages)
                }
            }
            
            result = await client.table('engrams').insert(engram_data).execute()
            
            if result.data:
                engram = result.data[0]
                compression_ratio = token_count / len(summary.split())
                
                # Log metrics
                await log_engram_created(
                    engram_id=engram['id'],
                    thread_id=thread_id,
                    trigger=trigger,
                    message_count=len(messages),
                    token_count=int(token_count),
                    surprise_score=surprise_score,
                    topics=topics,
                    compression_ratio=compression_ratio
                )
                
                logger.info(
                    f"Created engram {engram['id']} for thread {thread_id}: "
                    f"{len(messages)} messages, {token_count:.0f} tokens compressed to "
                    f"{len(summary.split())} words (ratio: {compression_ratio:.1f}:1)"
                )
                
                # Broadcast to dashboard for real-time visualization
                try:
                    from agentpress.engram_broadcaster import broadcast_engram_created
                    await broadcast_engram_created(engram)
                except Exception as e:
                    logger.debug(f"Could not broadcast engram creation: {e}")
                
                return engram
            else:
                logger.error("Failed to insert engram into database")
                return None
                
        except Exception as e:
            logger.error(f"Error creating engram: {e}", exc_info=True)
            return None
        finally:
            # Release lock
            self._consolidation_locks.pop(thread_id, None)
            
    async def _generate_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Generate a concise summary of the messages."""
        try:
            # Build conversation text
            conversation = []
            for msg in messages:
                content = msg.get('content', {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except:
                        content = {'content': content}
                
                role = content.get('role', msg.get('type', 'unknown'))
                text = content.get('content', '')
                
                if text:
                    conversation.append(f"{role.upper()}: {text[:500]}...")  # Truncate long messages
                    
            conversation_text = "\n\n".join(conversation[-10:])  # Last 10 messages max
            
            # Create summary prompt
            system_prompt = """You are a memory consolidation system. Create a concise summary that captures:
1. The main topic(s) discussed
2. Key decisions made or conclusions reached
3. Important technical details (errors, solutions, code snippets)
4. Emotional tone or user preferences expressed
5. Any unresolved questions or next steps

Be specific and factual. This summary will be used to maintain context in future conversations."""

            user_prompt = f"""Summarize this conversation segment into a memory engram (max 200 words):

{conversation_text}

SUMMARY:"""

            messages_for_llm = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use a fast model for summarization
            response = await make_llm_api_call(
                messages=messages_for_llm,
                model_name="gpt-4o-mini",
                max_tokens=300,
                temperature=0.3
            )
            
            if response and response.get('choices'):
                summary = response['choices'][0]['message']['content'].strip()
                return summary
            else:
                logger.error("No response from LLM for summary generation")
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return None
            
    async def _calculate_surprise_score(self, messages: List[Dict[str, Any]], summary: str) -> float:
        """
        Calculate how surprising/important this content is.
        Higher scores indicate content that should be prioritized for retention.
        """
        try:
            # Factors that increase surprise:
            surprise_factors = 0.0
            
            # 1. Sudden topic shifts
            topics = set()
            for msg in messages:
                content = str(msg.get('content', '')).lower()
                # Simple topic detection based on keywords
                if 'error' in content or 'exception' in content:
                    topics.add('error')
                if 'implement' in content or 'create' in content:
                    topics.add('implementation')
                if '?' in content:
                    topics.add('question')
                if '!' in content:
                    topics.add('exclamation')
                    
            topic_diversity = len(topics) / max(len(messages), 1)
            surprise_factors += topic_diversity * 0.3
            
            # 2. Emotional intensity (exclamations, capitals)
            emotional_intensity = sum(
                content.count('!') + (1 if content.isupper() else 0)
                for msg in messages
                for content in [str(msg.get('content', ''))]
            ) / max(len(messages), 1)
            surprise_factors += min(emotional_intensity * 0.2, 0.3)
            
            # 3. Code or technical content
            has_code = any('```' in str(msg.get('content', '')) for msg in messages)
            if has_code:
                surprise_factors += 0.2
                
            # 4. Error or problem-solving
            has_error = any('error' in str(msg.get('content', '')).lower() for msg in messages)
            if has_error:
                surprise_factors += 0.2
                
            # 5. Long messages (information density)
            avg_length = sum(len(str(msg.get('content', ''))) for msg in messages) / max(len(messages), 1)
            if avg_length > 500:
                surprise_factors += 0.1
                
            return min(surprise_factors, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating surprise score: {e}")
            return 0.5  # Default middle value
            
    async def _extract_topics(self, summary: str) -> List[str]:
        """Extract key topics from the summary."""
        try:
            # Simple keyword extraction
            keywords = []
            
            # Technical terms
            tech_terms = ['api', 'database', 'function', 'error', 'implementation', 
                         'bug', 'feature', 'performance', 'memory', 'token']
            for term in tech_terms:
                if term in summary.lower():
                    keywords.append(term)
                    
            # Action words
            action_words = ['create', 'implement', 'fix', 'debug', 'optimize', 
                           'design', 'build', 'deploy']
            for word in action_words:
                if word in summary.lower():
                    keywords.append(word)
                    
            # Limit to top 5 topics
            return keywords[:5]
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
            
    def _count_message_types(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count the types of messages in this segment."""
        type_counts = defaultdict(int)
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            type_counts[msg_type] += 1
        return dict(type_counts)
        
    async def retrieve_relevant_engrams(
        self,
        thread_id: str,
        query_context: Optional[str] = None,
        limit: int = MAX_ENGRAMS_IN_CONTEXT
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant engrams for the current context.
        
        Uses a combination of recency, relevance scores, and semantic similarity
        to select the best engrams to include in context.
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            client = await self.db.client
            
            # Get all active engrams for thread
            result = await client.table('engrams').select('*').eq(
                'thread_id', thread_id
            ).eq('is_deleted', False).execute()
            
            if not result.data:
                return []
                
            engrams = result.data
            total_available = len(engrams)
            
            # Apply decay to relevance scores
            now = datetime.now(timezone.utc)
            for engram in engrams:
                created = datetime.fromisoformat(engram['created_at'])
                days_old = (now - created).days
                
                # Apply exponential decay
                decayed_relevance = engram['relevance_score'] * (DECAY_RATE ** days_old)
                engram['current_relevance'] = decayed_relevance
                
            # Score engrams for retrieval
            scored_engrams = []
            for engram in engrams:
                score = self._calculate_retrieval_score(engram, query_context)
                scored_engrams.append((score, engram))
                
            # Sort by score and take top N
            scored_engrams.sort(key=lambda x: x[0], reverse=True)
            selected_engrams = [engram for score, engram in scored_engrams[:limit]]
            
            # Update access counts and last accessed
            for engram in selected_engrams:
                await client.table('engrams').update({
                    'access_count': engram['access_count'] + 1,
                    'relevance_score': min(engram['relevance_score'] + RELEVANCE_BOOST_ON_ACCESS, 5.0),
                    'last_accessed': now.isoformat()
                }).eq('id', engram['id']).execute()
                
            # Log retrieval metrics
            retrieval_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await log_engram_retrieved(
                thread_id=thread_id,
                query_tokens=len(query_context.split()) if query_context else 0,
                retrieved_engrams=selected_engrams,
                total_available=total_available,
                retrieval_time_ms=retrieval_time_ms
            )
            
            logger.debug(
                f"Retrieved {len(selected_engrams)} engrams from {total_available} available "
                f"for thread {thread_id} in {retrieval_time_ms:.1f}ms"
            )
            
            return selected_engrams
            
        except Exception as e:
            logger.error(f"Error retrieving engrams: {e}", exc_info=True)
            return []
            
    def _calculate_retrieval_score(self, engram: Dict[str, Any], query_context: Optional[str]) -> float:
        """
        Calculate a retrieval score for an engram based on multiple factors.
        
        Factors considered:
        1. Current relevance (with decay applied)
        2. Surprise score (important moments)
        3. Access frequency (Hebbian learning)
        4. Recency bonus
        5. Semantic similarity to query (if provided)
        """
        score = 0.0
        
        # 1. Current relevance (40% weight)
        score += engram.get('current_relevance', 0) * 0.4
        
        # 2. Surprise score (20% weight) - important moments
        score += engram.get('surprise_score', 0) * 0.2
        
        # 3. Access frequency (20% weight) - frequently accessed = important
        # Normalize by log to prevent runaway scores
        access_score = min(np.log1p(engram.get('access_count', 0)) / 3, 1.0)
        score += access_score * 0.2
        
        # 4. Recency bonus (10% weight)
        created = datetime.fromisoformat(engram['created_at'])
        hours_old = (datetime.now(timezone.utc) - created).total_seconds() / 3600
        recency_score = max(0, 1 - (hours_old / 168))  # Decay over a week
        score += recency_score * 0.1
        
        # 5. Semantic similarity (10% weight) if query provided
        if query_context and query_context.strip():
            similarity = self._calculate_simple_similarity(engram['content'], query_context)
            score += similarity * 0.1
            
        return score
        
    def _calculate_simple_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple keyword-based similarity between texts.
        
        In a production system, this would use embeddings, but for now
        we use keyword overlap.
        """
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                    'to', 'for', 'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were'}
        words1 = words1 - stopwords
        words2 = words2 - stopwords
        
        if not words1 or not words2:
            return 0.0
            
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
        
    async def check_and_consolidate(
        self,
        thread_id: str,
        current_token_count: int,
        recent_messages: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if consolidation is needed and perform it if necessary.
        
        This is the main entry point called by the context manager.
        """
        try:
            # Check if we've hit the token threshold
            if current_token_count >= ENGRAM_CHUNK_SIZE:
                logger.info(f"Token threshold reached for thread {thread_id}: {current_token_count} tokens")
                return await self.create_engram(
                    thread_id=thread_id,
                    messages=recent_messages,
                    trigger="token_threshold"
                )
                
            # Check for surprise-triggered consolidation
            if len(recent_messages) >= MIN_MESSAGES_FOR_ENGRAM:
                # Quick surprise check on recent messages
                surprise = await self._calculate_surprise_score(recent_messages, "")
                if surprise >= SURPRISE_THRESHOLD:
                    logger.info(f"Surprise threshold reached for thread {thread_id}: score={surprise:.2f}")
                    return await self.create_engram(
                        thread_id=thread_id,
                        messages=recent_messages,
                        trigger="surprise"
                    )
                    
            return None
            
        except Exception as e:
            logger.error(f"Error in check_and_consolidate: {e}", exc_info=True)
            return None
            
    async def get_context_summary(self, thread_id: str) -> str:
        """
        Get a formatted summary of relevant engrams for inclusion in context.
        
        This is what actually gets injected into the conversation context.
        """
        try:
            engrams = await self.retrieve_relevant_engrams(thread_id)
            
            if not engrams:
                return ""
                
            # Format engrams for context
            summary_parts = ["# Previous Context\n"]
            
            for i, engram in enumerate(engrams, 1):
                created = datetime.fromisoformat(engram['created_at'])
                age = (datetime.now(timezone.utc) - created).days
                
                summary_parts.append(f"## Memory {i} ({age} days ago)")
                summary_parts.append(engram['content'])
                
                # Add metadata if relevant
                metadata = engram.get('metadata', {})
                if metadata.get('has_error'):
                    summary_parts.append("*Note: This memory contains error handling context*")
                if metadata.get('has_code'):
                    summary_parts.append("*Note: This memory contains code examples*")
                    
                summary_parts.append("")  # Blank line
                
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}", exc_info=True)
            return ""
            
    async def cleanup_old_engrams(self, days_to_keep: int = 30) -> int:
        """
        Soft delete engrams older than specified days with very low relevance.
        
        Returns number of engrams cleaned up.
        """
        try:
            client = await self.db.client
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            # Only delete engrams that are old AND have low relevance
            result = await client.table('engrams').update({
                'is_deleted': True
            }).lt('created_at', cutoff_date.isoformat()).lt('relevance_score', 0.1).execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {count} old engrams")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up engrams: {e}", exc_info=True)
            return 0


# Singleton instance
_engram_manager = None

def get_engram_manager() -> EngramManager:
    """Get or create the singleton EngramManager instance."""
    global _engram_manager
    if _engram_manager is None:
        _engram_manager = EngramManager()
    return _engram_manager