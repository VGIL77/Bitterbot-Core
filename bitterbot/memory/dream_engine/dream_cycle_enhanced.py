"""
Enhanced Dream Cycle for BitterBot Memory System.

This implements the "dream" phase where the system consolidates memories,
discovers patterns, and generates insights during idle time.

Inspired by:
- REM sleep memory consolidation in humans
- Offline reinforcement learning
- Curiosity-driven exploration
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json

from backend.services.supabase import DBConnection
from backend.services.llm import make_llm_api_call
from backend.utils.logger import logger


class EnhancedDreamCycle:
    """
    Manages autonomous memory consolidation and insight generation.
    
    During "dream" cycles, the system:
    1. Reviews high-curiosity episodes
    2. Identifies patterns across engrams
    3. Generates hypothetical scenarios
    4. Consolidates redundant memories
    5. Creates new connections between concepts
    """
    
    def __init__(self, memory_system):
        self.memory = memory_system
        self.db = DBConnection()
        self.is_dreaming = False
        self.dream_count = 0
        self.dream_log = []
        self.min_idle_time = 300  # 5 minutes of idle before dreaming
        self.dream_interval = 600  # 10 minutes between dream cycles
        
    async def start_dreaming(self):
        """Start autonomous dream cycles during idle periods."""
        if self.is_dreaming:
            logger.warning("Dream cycle already active")
            return
            
        self.is_dreaming = True
        logger.info("💭 Entering dream state...")
        
        try:
            while self.is_dreaming:
                await self._dream_cycle()
                await asyncio.sleep(self.dream_interval)
        except Exception as e:
            logger.error(f"Dream cycle error: {e}", exc_info=True)
        finally:
            self.is_dreaming = False
            logger.info("😴 Exiting dream state")
    
    async def _dream_cycle(self):
        """Execute a single dream cycle."""
        self.dream_count += 1
        cycle_start = datetime.now(timezone.utc)
        
        logger.info(f"🌙 Dream cycle {self.dream_count} beginning...")
        
        dream_results = {
            'cycle': self.dream_count,
            'timestamp': cycle_start.isoformat(),
            'insights': [],
            'connections': [],
            'consolidations': []
        }
        
        try:
            # Phase 1: Memory Replay (review high-curiosity engrams)
            curious_engrams = await self._find_curious_engrams()
            logger.debug(f"Found {len(curious_engrams)} curious engrams to explore")
            
            # Phase 2: Pattern Recognition (find connections between engrams)
            if len(curious_engrams) >= 2:
                connections = await self._find_connections(curious_engrams)
                dream_results['connections'] = connections
                
            # Phase 3: Hypothetical Exploration (what-if scenarios)
            if curious_engrams:
                insights = await self._explore_hypotheticals(curious_engrams[:3])
                dream_results['insights'] = insights
                
            # Phase 4: Memory Consolidation (merge similar engrams)
            consolidations = await self._consolidate_similar_memories()
            dream_results['consolidations'] = consolidations
            
            # Phase 5: Curiosity Generation (identify knowledge gaps)
            curiosity_seeds = await self._generate_curiosity_seeds(curious_engrams)
            dream_results['curiosity_seeds'] = curiosity_seeds
            
            # Log dream results
            self.dream_log.append(dream_results)
            await self._save_dream_log(dream_results)
            
            cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
            logger.info(
                f"✨ Dream cycle {self.dream_count} complete in {cycle_duration:.1f}s: "
                f"{len(dream_results['insights'])} insights, "
                f"{len(dream_results['connections'])} connections, "
                f"{len(dream_results['consolidations'])} consolidations"
            )
            
        except Exception as e:
            logger.error(f"Error in dream cycle: {e}", exc_info=True)
    
    async def _find_curious_engrams(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find engrams with high curiosity potential."""
        try:
            client = await self.db.client
            
            # Query for high-surprise, low-access engrams (unexplored territory)
            result = await client.table('engrams')\
                .select('*')\
                .gte('surprise_score', 0.6)\
                .lte('access_count', 3)\
                .eq('is_deleted', False)\
                .order('surprise_score', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error finding curious engrams: {e}")
            return []
    
    async def _find_connections(self, engrams: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Discover connections between seemingly unrelated engrams."""
        connections = []
        
        try:
            # Prepare engram summaries for analysis
            engram_texts = []
            for eng in engrams[:5]:  # Limit to prevent token overflow
                metadata = eng.get('metadata', {})
                topics = metadata.get('topics', [])
                engram_texts.append({
                    'id': eng['id'],
                    'content': eng['content'][:200],
                    'topics': topics
                })
            
            # Ask LLM to find non-obvious connections
            system_prompt = """You are a pattern recognition system exploring connections between memories.
Find non-obvious relationships, shared themes, or potential insights that connect these memory fragments.
Focus on conceptual bridges, not just keyword matches.

Output format:
{
    "connections": [
        {
            "engram1_id": "id1",
            "engram2_id": "id2", 
            "connection_type": "conceptual/causal/thematic/methodological",
            "description": "Brief description of the connection",
            "insight": "What this connection reveals"
        }
    ]
}"""

            user_prompt = f"Find connections between these memory engrams:\n{json.dumps(engram_texts, indent=2)}"
            
            response = await make_llm_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model_name="gpt-4o-mini",
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            if response and response.get('choices'):
                result = json.loads(response['choices'][0]['message']['content'])
                connections = result.get('connections', [])
                
        except Exception as e:
            logger.error(f"Error finding connections: {e}")
            
        return connections
    
    async def _explore_hypotheticals(self, engrams: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate 'what-if' scenarios based on engram content."""
        insights = []
        
        try:
            # Prepare context from engrams
            context = "\n\n".join([
                f"Memory {i+1}: {eng['content'][:300]}..."
                for i, eng in enumerate(engrams)
            ])
            
            system_prompt = """You are a creative hypothesis generator.
Based on the given memories, generate insightful "what-if" questions and potential explorations.
Focus on:
- Unexplored implications
- Alternative approaches
- Potential optimizations
- Edge cases not considered

Output format:
{
    "hypotheticals": [
        {
            "question": "What if...",
            "exploration": "This could lead to...",
            "value": "high/medium/low"
        }
    ]
}"""

            response = await make_llm_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate hypotheticals from:\n{context}"}
                ],
                model_name="gpt-4o-mini",
                temperature=0.8,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            if response and response.get('choices'):
                result = json.loads(response['choices'][0]['message']['content'])
                insights = result.get('hypotheticals', [])
                
        except Exception as e:
            logger.error(f"Error exploring hypotheticals: {e}")
            
        return insights
    
    async def _consolidate_similar_memories(self) -> List[Dict[str, Any]]:
        """Identify and merge highly similar engrams."""
        consolidations = []
        
        try:
            client = await self.db.client
            
            # Get recent engrams from the same threads
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            result = await client.table('engrams')\
                .select('thread_id, content, id, metadata')\
                .gte('created_at', week_ago)\
                .eq('is_deleted', False)\
                .execute()
            
            if not result.data:
                return []
            
            # Group by thread
            by_thread = {}
            for eng in result.data:
                thread_id = eng['thread_id']
                if thread_id not in by_thread:
                    by_thread[thread_id] = []
                by_thread[thread_id].append(eng)
            
            # Check for redundancy within each thread
            for thread_id, thread_engrams in by_thread.items():
                if len(thread_engrams) < 3:
                    continue
                    
                # Simple similarity check (in production, use embeddings)
                for i in range(len(thread_engrams)):
                    for j in range(i + 1, len(thread_engrams)):
                        eng1 = thread_engrams[i]
                        eng2 = thread_engrams[j]
                        
                        # Check topic overlap
                        topics1 = set(eng1.get('metadata', {}).get('topics', []))
                        topics2 = set(eng2.get('metadata', {}).get('topics', []))
                        
                        if topics1 and topics2:
                            overlap = len(topics1 & topics2) / len(topics1 | topics2)
                            
                            if overlap > 0.7:  # High similarity
                                consolidations.append({
                                    'type': 'redundancy_detected',
                                    'engram1': eng1['id'],
                                    'engram2': eng2['id'],
                                    'similarity': overlap,
                                    'action': 'merge_candidate'
                                })
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            
        return consolidations
    
    async def _generate_curiosity_seeds(self, engrams: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify knowledge gaps and questions for future exploration."""
        seeds = []
        
        try:
            # Analyze engrams for unanswered questions
            for eng in engrams[:5]:
                content = eng['content']
                metadata = eng.get('metadata', {})
                
                # Look for question marks or uncertainty indicators
                if '?' in content or 'unclear' in content.lower() or 'todo' in content.lower():
                    seeds.append({
                        'type': 'unanswered_question',
                        'engram_id': eng['id'],
                        'curiosity_level': 'high',
                        'topic': metadata.get('topics', ['unknown'])[0]
                    })
                
                # Look for errors without solutions
                if metadata.get('has_error', False):
                    seeds.append({
                        'type': 'unresolved_error',
                        'engram_id': eng['id'],
                        'curiosity_level': 'medium',
                        'topic': 'error_handling'
                    })
            
        except Exception as e:
            logger.error(f"Error generating curiosity seeds: {e}")
            
        return seeds
    
    async def _save_dream_log(self, dream_results: Dict[str, Any]):
        """Persist dream results for analysis."""
        try:
            # Store in dream memory (when implemented)
            if hasattr(self.memory, 'dream_memory'):
                await self.memory.dream_memory.store_dream(dream_results)
            
            # For now, just log it
            logger.debug(f"Dream log: {json.dumps(dream_results, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error saving dream log: {e}")
    
    def stop_dreaming(self):
        """Stop the dream cycles."""
        self.is_dreaming = False
        logger.info(f"Dream cycles stopped. Total dreams: {self.dream_count}")
    
    async def get_dream_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent insights from dream cycles."""
        insights = []
        
        for dream in reversed(self.dream_log[-5:]):  # Last 5 dreams
            insights.extend(dream.get('insights', []))
            
        return insights[:limit]
    
    async def trigger_lucid_dream(self, focus_topic: str) -> Dict[str, Any]:
        """Trigger a focused dream cycle on a specific topic."""
        logger.info(f"🎯 Triggering lucid dream on topic: {focus_topic}")
        
        try:
            client = await self.db.client
            
            # Find engrams related to the topic
            result = await client.table('engrams')\
                .select('*')\
                .contains('metadata->topics', [focus_topic])\
                .eq('is_deleted', False)\
                .limit(10)\
                .execute()
            
            if result.data:
                # Run focused exploration
                insights = await self._explore_hypotheticals(result.data[:3])
                connections = await self._find_connections(result.data)
                
                return {
                    'topic': focus_topic,
                    'insights': insights,
                    'connections': connections,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.warning(f"No engrams found for topic: {focus_topic}")
                return {'topic': focus_topic, 'insights': [], 'connections': []}
                
        except Exception as e:
            logger.error(f"Error in lucid dream: {e}")
            return {'error': str(e)}