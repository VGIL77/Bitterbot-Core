"""
Improved Engram Memory Management System.

Key improvements:
- Accurate token counting using tiktoken
- Embeddings for semantic similarity
- Caching for performance
- Better error handling
- Batch processing support
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from collections import defaultdict
import numpy as np
from functools import lru_cache
import tiktoken

from services.supabase import DBConnection
from services.llm import make_llm_api_call
from utils.logger import logger
from sentence_transformers import SentenceTransformer

# Configuration constants
ENGRAM_CHUNK_SIZE = 5000  # Create engram every 5k tokens
DECAY_RATE = 0.95  # Daily decay rate for relevance scores
MAX_ENGRAMS_IN_CONTEXT = 5  # Maximum engrams to include in context
SURPRISE_THRESHOLD = 0.7  # Threshold for surprise-triggered consolidation
MIN_MESSAGES_FOR_ENGRAM = 3  # Minimum messages to create an engram
RELEVANCE_BOOST_ON_ACCESS = 0.2  # Boost to relevance when accessed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality embeddings
CACHE_TTL_SECONDS = 300  # 5 minute cache for embeddings


class ImprovedEngramManager:
    """
    Enhanced engram manager with better performance and accuracy.
    """
    
    def __init__(self):
        self.db = DBConnection()
        self._consolidation_locks = {}
        self._embedding_model = None
        self._tokenizer = None
        self._embedding_cache = {}
        self._cache_timestamps = {}
        
    @property
    def embedding_model(self):
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        return self._embedding_model
    
    @property
    def tokenizer(self):
        """Lazy load the tokenizer."""
        if self._tokenizer is None:
            # Use cl100k_base tokenizer (GPT-4)
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        return self._tokenizer
    
    def count_tokens(self, text: str) -> int:
        """Accurately count tokens using tiktoken."""
        return len(self.tokenizer.encode(text))
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching."""
        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._embedding_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if datetime.now().timestamp() - timestamp < CACHE_TTL_SECONDS:
                return self._embedding_cache[cache_key]
        
        # Generate embedding
        embedding = self.embedding_model.encode(text)
        
        # Cache it
        self._embedding_cache[cache_key] = embedding
        self._cache_timestamps[cache_key] = datetime.now().timestamp()
        
        # Clean old cache entries if too many
        if len(self._embedding_cache) > 1000:
            self._clean_cache()
            
        return embedding
    
    def _clean_cache(self):
        """Remove old cache entries."""
        current_time = datetime.now().timestamp()
        keys_to_remove = []
        
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp > CACHE_TTL_SECONDS:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._embedding_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
    
    async def create_engram_with_embeddings(
        self,
        thread_id: str,
        messages: List[Dict[str, Any]],
        trigger: str = "token_threshold",
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Enhanced engram creation with embeddings."""
        
        # Prevent concurrent consolidations
        if thread_id in self._consolidation_locks:
            logger.warning(f"Consolidation already in progress for thread {thread_id}")
            return None
            
        self._consolidation_locks[thread_id] = True
        
        try:
            # Validate messages
            if len(messages) < MIN_MESSAGES_FOR_ENGRAM and not force:
                return None
            
            # Calculate accurate token count
            full_text = " ".join(
                str(msg.get('content', '')) for msg in messages
            )
            token_count = self.count_tokens(full_text)
            
            # Generate summary
            summary = await self._generate_enhanced_summary(messages)
            if not summary:
                return None
            
            # Generate embedding for the summary
            summary_embedding = self.get_embedding(summary)
            
            # Calculate surprise score with context
            surprise_score = await self._calculate_contextual_surprise(
                messages, summary, thread_id
            )
            
            # Extract topics using NLP
            topics = self._extract_topics_nlp(summary)
            
            # Prepare engram data
            client = await self.db.client
            
            engram_data = {
                "thread_id": thread_id,
                "content": summary,
                "message_range": {
                    "start": messages[0].get('message_id'),
                    "end": messages[-1].get('message_id'),
                    "count": len(messages)
                },
                "token_count": token_count,
                "relevance_score": 1.0,
                "surprise_score": surprise_score,
                "access_count": 0,
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "trigger": trigger,
                    "topics": topics,
                    "message_types": self._count_message_types(messages),
                    "has_code": any("```" in str(msg.get('content', '')) for msg in messages),
                    "has_error": any("error" in str(msg.get('content', '')).lower() for msg in messages),
                    "embedding_model": EMBEDDING_MODEL,
                    "summary_tokens": self.count_tokens(summary)
                }
            }
            
            # Store engram
            result = await client.table('engrams').insert(engram_data).execute()
            
            if result.data:
                engram = result.data[0]
                
                # Store embedding separately (if using vector DB)
                await self._store_embedding(engram['id'], summary_embedding)
                
                compression_ratio = token_count / self.count_tokens(summary)
                
                logger.info(
                    f"Created engram {engram['id']}: {token_count} tokens → "
                    f"{engram_data['metadata']['summary_tokens']} tokens "
                    f"(compression: {compression_ratio:.1f}:1)"
                )
                
                return engram
                
        except Exception as e:
            logger.error(f"Error creating engram: {e}", exc_info=True)
            return None
        finally:
            self._consolidation_locks.pop(thread_id, None)
    
    async def _generate_enhanced_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Generate better summaries with structured extraction."""
        
        # Build conversation with token limits
        conversation_parts = []
        token_budget = 2000  # Leave room for summary
        current_tokens = 0
        
        for msg in reversed(messages):  # Start from most recent
            content = str(msg.get('content', {}).get('content', ''))
            msg_tokens = self.count_tokens(content)
            
            if current_tokens + msg_tokens > token_budget:
                break
                
            role = msg.get('content', {}).get('role', 'unknown')
            conversation_parts.insert(0, f"{role.upper()}: {content}")
            current_tokens += msg_tokens
        
        conversation_text = "\n\n".join(conversation_parts)
        
        system_prompt = """You are an advanced memory consolidation system. Create a structured summary that captures:

FORMAT YOUR RESPONSE AS JSON:
{
    "main_topics": ["topic1", "topic2"],
    "key_decisions": ["decision1", "decision2"],
    "technical_details": {
        "errors": ["error1"],
        "solutions": ["solution1"],
        "code_snippets": ["snippet1"]
    },
    "user_preferences": ["preference1"],
    "unresolved_questions": ["question1"],
    "emotional_tone": "neutral/positive/frustrated/confused",
    "summary": "A concise narrative summary (max 150 words)"
}

Be specific and factual. Focus on information needed to continue the conversation later."""

        try:
            response = await make_llm_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Summarize this conversation:\n\n{conversation_text}"}
                ],
                model_name="gpt-4o-mini",
                max_tokens=400,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            if response and response.get('choices'):
                result = json.loads(response['choices'][0]['message']['content'])
                return result.get('summary', '')
                
        except Exception as e:
            logger.error(f"Error generating enhanced summary: {e}")
            
        return None
    
    async def _calculate_contextual_surprise(
        self, 
        messages: List[Dict[str, Any]], 
        summary: str,
        thread_id: str
    ) -> float:
        """Calculate surprise with context awareness."""
        
        base_surprise = 0.0
        
        # Get recent engrams for context
        try:
            client = await self.db.client
            recent_engrams = await client.table('engrams')\
                .select('content, topics')\
                .eq('thread_id', thread_id)\
                .order('created_at', desc=True)\
                .limit(5)\
                .execute()
            
            if recent_engrams.data:
                # Check for topic shifts
                recent_topics = set()
                for engram in recent_engrams.data:
                    topics = engram.get('metadata', {}).get('topics', [])
                    recent_topics.update(topics)
                
                current_topics = set(self._extract_topics_nlp(summary))
                new_topics = current_topics - recent_topics
                
                # More new topics = higher surprise
                topic_novelty = len(new_topics) / max(len(current_topics), 1)
                base_surprise += topic_novelty * 0.4
                
        except Exception as e:
            logger.error(f"Error calculating contextual surprise: {e}")
        
        # Original surprise factors
        for msg in messages:
            content = str(msg.get('content', '')).lower()
            
            # Error detection (high priority)
            if any(word in content for word in ['error', 'exception', 'failed', 'bug']):
                base_surprise += 0.3
                break
            
            # Question detection
            if '?' in content:
                base_surprise += 0.1
            
            # Code detection
            if '```' in content or 'def ' in content or 'function' in content:
                base_surprise += 0.2
                
        return min(base_surprise, 1.0)
    
    def _extract_topics_nlp(self, text: str) -> List[str]:
        """Extract topics using simple NLP techniques."""
        # In production, use spaCy or similar for better extraction
        
        topics = []
        text_lower = text.lower()
        
        # Domain-specific keyword lists
        tech_keywords = {
            'api': ['api', 'endpoint', 'request', 'response'],
            'database': ['database', 'query', 'table', 'sql'],
            'error': ['error', 'exception', 'bug', 'issue'],
            'frontend': ['ui', 'component', 'react', 'vue'],
            'backend': ['server', 'backend', 'node', 'python'],
            'deployment': ['deploy', 'docker', 'kubernetes', 'ci/cd'],
            'performance': ['performance', 'optimize', 'slow', 'fast'],
            'security': ['security', 'auth', 'permission', 'token']
        }
        
        for topic, keywords in tech_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:5]  # Limit to 5 topics
    
    async def _store_embedding(self, engram_id: str, embedding: np.ndarray):
        """Store embedding in vector database."""
        # TODO: Implement actual vector storage
        # For now, we could store in a separate table or use pgvector
        pass
    
    async def retrieve_with_embeddings(
        self,
        thread_id: str,
        query_context: Optional[str] = None,
        limit: int = MAX_ENGRAMS_IN_CONTEXT
    ) -> List[Dict[str, Any]]:
        """Retrieve engrams using semantic similarity."""
        
        try:
            client = await self.db.client
            
            # Get all active engrams
            result = await client.table('engrams')\
                .select('*')\
                .eq('thread_id', thread_id)\
                .eq('is_deleted', False)\
                .execute()
            
            if not result.data:
                return []
            
            engrams = result.data
            
            # If we have query context, use embeddings
            if query_context:
                query_embedding = self.get_embedding(query_context)
                
                # Calculate semantic similarities
                for engram in engrams:
                    engram_embedding = self.get_embedding(engram['content'])
                    
                    # Cosine similarity
                    similarity = np.dot(query_embedding, engram_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(engram_embedding)
                    )
                    engram['semantic_similarity'] = float(similarity)
            
            # Apply decay and calculate scores
            now = datetime.now(timezone.utc)
            scored_engrams = []
            
            for engram in engrams:
                created = datetime.fromisoformat(engram['created_at'])
                days_old = (now - created).days
                
                # Calculate composite score
                score = self._calculate_enhanced_retrieval_score(
                    engram, days_old, query_context is not None
                )
                scored_engrams.append((score, engram))
            
            # Sort and select top engrams
            scored_engrams.sort(key=lambda x: x[0], reverse=True)
            selected_engrams = [engram for score, engram in scored_engrams[:limit]]
            
            # Update access patterns
            await self._update_access_patterns(selected_engrams)
            
            return selected_engrams
            
        except Exception as e:
            logger.error(f"Error retrieving engrams: {e}", exc_info=True)
            return []
    
    def _calculate_enhanced_retrieval_score(
        self, 
        engram: Dict[str, Any], 
        days_old: int,
        has_query: bool
    ) -> float:
        """Enhanced scoring with semantic similarity."""
        
        # Base relevance with decay
        decayed_relevance = engram['relevance_score'] * (DECAY_RATE ** days_old)
        score = decayed_relevance * 0.3
        
        # Surprise/importance
        score += engram.get('surprise_score', 0) * 0.2
        
        # Access frequency (Hebbian)
        access_score = min(np.log1p(engram.get('access_count', 0)) / 3, 1.0)
        score += access_score * 0.15
        
        # Recency
        recency_score = max(0, 1 - (days_old / 30))  # 30-day window
        score += recency_score * 0.1
        
        # Semantic similarity (if available)
        if has_query and 'semantic_similarity' in engram:
            score += engram['semantic_similarity'] * 0.25
        else:
            # Give more weight to other factors if no query
            score *= 1.33
            
        return score
    
    async def _update_access_patterns(self, engrams: List[Dict[str, Any]]):
        """Batch update access patterns for efficiency."""
        if not engrams:
            return
            
        try:
            client = await self.db.client
            now = datetime.now(timezone.utc).isoformat()
            
            # Batch update
            for engram in engrams:
                new_relevance = min(
                    engram['relevance_score'] + RELEVANCE_BOOST_ON_ACCESS, 
                    5.0
                )
                
                await client.table('engrams').update({
                    'access_count': engram['access_count'] + 1,
                    'relevance_score': new_relevance,
                    'last_accessed': now
                }).eq('id', engram['id']).execute()
                
        except Exception as e:
            logger.error(f"Error updating access patterns: {e}")


# Singleton instance
_improved_engram_manager = None

def get_improved_engram_manager() -> ImprovedEngramManager:
    """Get or create the singleton improved EngramManager instance."""
    global _improved_engram_manager
    if _improved_engram_manager is None:
        _improved_engram_manager = ImprovedEngramManager()
    return _improved_engram_manager