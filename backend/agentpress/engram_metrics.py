"""
Engram Metrics Collection and Analysis.

This module provides comprehensive metrics for the engram memory system,
including neuroscience-inspired measurements and academic-grade statistics.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import json

from services.supabase import DBConnection
from utils.logger import logger


async def log_engram_created(engram_id: str, thread_id: str, **kwargs):
    """Log when an engram is created."""
    logger.info(f"Engram created: {engram_id} for thread {thread_id}", extra=kwargs)


async def log_engram_retrieved(engram_id: str, thread_id: str, **kwargs):
    """Log when an engram is retrieved."""
    logger.info(f"Engram retrieved: {engram_id} for thread {thread_id}", extra=kwargs)


class EngramMetrics:
    """Basic metrics for engram system."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def get_basic_stats(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Get basic statistics about engrams."""
        client = await self.db.client
        
        try:
            query = client.table('engrams').select('*')
            if thread_id:
                query = query.eq('thread_id', thread_id)
                
            result = await query.execute()
            
            if not result.data:
                return {
                    'total_engrams': 0,
                    'avg_relevance_score': 0.0,
                    'avg_surprise_score': 0.0,
                    'total_tokens': 0,
                    'compression_ratio': 0.0
                }
            
            engrams = result.data
            total_tokens = sum(e.get('token_count', 0) for e in engrams)
            content_length = sum(len(e.get('content', '')) for e in engrams)
            
            return {
                'total_engrams': len(engrams),
                'avg_relevance_score': np.mean([e.get('relevance_score', 0) for e in engrams]),
                'avg_surprise_score': np.mean([e.get('surprise_score', 0) for e in engrams]),
                'total_tokens': total_tokens,
                'compression_ratio': total_tokens / content_length if content_length > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            return {}


class MemoryHealthMetrics:
    """Analyze memory health and diversity."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_diversity_index(self, thread_id: str) -> float:
        """Calculate diversity of engram content using Shannon entropy."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('content', 'relevance_score')\
                .eq('thread_id', thread_id)\
                .execute()
                
            if not result.data:
                return 0.0
                
            # Simple diversity based on content length distribution
            lengths = [len(e['content']) for e in result.data]
            if not lengths:
                return 0.0
                
            # Normalize and calculate entropy
            total = sum(lengths)
            probs = [l/total for l in lengths]
            entropy = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
            
            # Normalize to 0-1 range
            max_entropy = np.log2(len(lengths))
            return entropy / max_entropy if max_entropy > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating diversity: {e}")
            return 0.0
            
    async def analyze_temporal_distribution(self, thread_id: str) -> Dict[str, Any]:
        """Analyze how engrams are distributed over time."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('created_at')\
                .eq('thread_id', thread_id)\
                .order('created_at')\
                .execute()
                
            if not result.data or len(result.data) < 2:
                return {'distribution': 'insufficient_data'}
                
            # Calculate time gaps
            times = [datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')) 
                    for e in result.data]
            gaps = [(times[i+1] - times[i]).total_seconds() 
                   for i in range(len(times)-1)]
            
            avg_gap = np.mean(gaps)
            std_gap = np.std(gaps)
            
            return {
                'distribution': 'uniform' if std_gap < avg_gap * 0.5 else 'bursty',
                'avg_gap_seconds': avg_gap,
                'std_gap_seconds': std_gap,
                'total_duration_hours': (times[-1] - times[0]).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal distribution: {e}")
            return {'distribution': 'error'}
            
    async def analyze_decay_patterns(self, thread_id: str) -> Dict[str, Any]:
        """Analyze relevance decay patterns."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('relevance_score', 'created_at', 'last_accessed')\
                .eq('thread_id', thread_id)\
                .execute()
                
            if not result.data:
                return {'pattern': 'no_data'}
                
            # Group by age and calculate average relevance
            now = datetime.now(timezone.utc)
            age_relevance = []
            
            for engram in result.data:
                created = datetime.fromisoformat(engram['created_at'].replace('Z', '+00:00'))
                age_days = (now - created).days
                relevance = engram['relevance_score']
                age_relevance.append((age_days, relevance))
                
            if not age_relevance:
                return {'pattern': 'no_decay_data'}
                
            # Fit exponential decay if enough data
            if len(age_relevance) > 5:
                ages, relevances = zip(*age_relevance)
                # Simple linear regression on log scale
                log_relevances = [np.log(r) if r > 0 else -10 for r in relevances]
                decay_rate = np.polyfit(ages, log_relevances, 1)[0]
                
                return {
                    'pattern': 'exponential',
                    'decay_rate': -decay_rate,  # Positive for decay
                    'half_life_days': 0.693 / -decay_rate if decay_rate < 0 else float('inf')
                }
            else:
                return {'pattern': 'insufficient_data'}
                
        except Exception as e:
            logger.error(f"Error analyzing decay patterns: {e}")
            return {'pattern': 'error'}


class CognitiveLoadMetrics:
    """Measure cognitive load and processing efficiency."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def get_current_load(self, thread_id: str) -> Dict[str, Any]:
        """Calculate current cognitive load for a thread."""
        client = await self.db.client
        
        try:
            # Get recent engrams (last hour)
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            result = await client.table('engrams')\
                .select('token_count', 'surprise_score')\
                .eq('thread_id', thread_id)\
                .gte('created_at', one_hour_ago)\
                .execute()
                
            if not result.data:
                return {'current_load': 0.0, 'status': 'idle'}
                
            # Calculate load based on token rate and surprise
            total_tokens = sum(e['token_count'] for e in result.data)
            avg_surprise = np.mean([e['surprise_score'] for e in result.data])
            
            # Load = tokens/hour * surprise factor
            load = (total_tokens / 1000) * (1 + avg_surprise)
            
            status = 'low' if load < 5 else 'medium' if load < 20 else 'high'
            
            return {
                'current_load': load,
                'status': status,
                'tokens_per_hour': total_tokens,
                'surprise_factor': avg_surprise
            }
            
        except Exception as e:
            logger.error(f"Error calculating cognitive load: {e}")
            return {'current_load': 0.0, 'status': 'error'}


class NeuroscienceMetrics:
    """Neuroscience-inspired metrics."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_hebbian_strength(self, thread_id: str) -> float:
        """Calculate Hebbian connection strength based on co-access patterns."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('id', 'access_count', 'last_accessed')\
                .eq('thread_id', thread_id)\
                .order('last_accessed', desc=True)\
                .limit(20)\
                .execute()
                
            if not result.data or len(result.data) < 2:
                return 0.0
                
            # Calculate co-access strength
            total_strength = 0
            pairs = 0
            
            for i in range(len(result.data)-1):
                for j in range(i+1, len(result.data)):
                    # Strength based on access counts and temporal proximity
                    access_product = result.data[i]['access_count'] * result.data[j]['access_count']
                    
                    if result.data[i]['last_accessed'] and result.data[j]['last_accessed']:
                        time1 = datetime.fromisoformat(result.data[i]['last_accessed'].replace('Z', '+00:00'))
                        time2 = datetime.fromisoformat(result.data[j]['last_accessed'].replace('Z', '+00:00'))
                        time_diff = abs((time1 - time2).total_seconds())
                        
                        # Decay with time difference (1 hour half-life)
                        temporal_factor = np.exp(-time_diff / 3600)
                        strength = access_product * temporal_factor
                        
                        total_strength += strength
                        pairs += 1
                        
            return total_strength / pairs if pairs > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating Hebbian strength: {e}")
            return 0.0
            
    async def analyze_surprise_effectiveness(self, thread_id: str) -> Dict[str, Any]:
        """Analyze how well surprise scores predict future access."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('surprise_score', 'access_count')\
                .eq('thread_id', thread_id)\
                .execute()
                
            if not result.data or len(result.data) < 5:
                return {'correlation': 0.0, 'effectiveness': 'unknown'}
                
            surprises = [e['surprise_score'] for e in result.data]
            accesses = [e['access_count'] for e in result.data]
            
            # Calculate correlation
            correlation = np.corrcoef(surprises, accesses)[0, 1]
            
            effectiveness = 'high' if abs(correlation) > 0.5 else 'medium' if abs(correlation) > 0.3 else 'low'
            
            return {
                'correlation': correlation,
                'effectiveness': effectiveness,
                'sample_size': len(result.data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing surprise effectiveness: {e}")
            return {'correlation': 0.0, 'effectiveness': 'error'}
            
    async def detect_consolidation_patterns(self, thread_id: str) -> List[Dict[str, Any]]:
        """Detect patterns in memory consolidation."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('created_at', 'token_count', 'trigger')\
                .eq('thread_id', thread_id)\
                .order('created_at')\
                .execute()
                
            if not result.data or len(result.data) < 3:
                return []
                
            patterns = []
            
            # Detect bursts
            times = [datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')) 
                    for e in result.data]
            
            for i in range(1, len(times)-1):
                gap1 = (times[i] - times[i-1]).total_seconds()
                gap2 = (times[i+1] - times[i]).total_seconds()
                
                if gap1 < 300 and gap2 < 300:  # Within 5 minutes
                    patterns.append({
                        'type': 'burst',
                        'start': times[i-1].isoformat(),
                        'end': times[i+1].isoformat(),
                        'engram_count': 3
                    })
                    
            # Detect regular intervals
            gaps = [(times[i+1] - times[i]).total_seconds() for i in range(len(times)-1)]
            if len(gaps) > 5:
                avg_gap = np.mean(gaps)
                std_gap = np.std(gaps)
                
                if std_gap < avg_gap * 0.2:  # Low variance
                    patterns.append({
                        'type': 'regular',
                        'interval_seconds': avg_gap,
                        'consistency': 1 - (std_gap / avg_gap)
                    })
                    
            return patterns[:5]  # Return top 5 patterns
            
        except Exception as e:
            logger.error(f"Error detecting consolidation patterns: {e}")
            return []


class ExperienceMetrics:
    """User experience and system performance metrics."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def measure_retrieval_latency(self, thread_id: str) -> Dict[str, Any]:
        """Measure retrieval performance (simulated for now)."""
        # In production, this would measure actual retrieval times
        return {
            'avg_latency_ms': 25.0,
            'p95_latency_ms': 45.0,
            'p99_latency_ms': 120.0
        }
        
    async def measure_context_continuity(self, thread_id: str) -> float:
        """Measure how well context is maintained across engrams."""
        client = await self.db.client
        
        try:
            result = await client.table('engrams')\
                .select('content')\
                .eq('thread_id', thread_id)\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
                
            if not result.data or len(result.data) < 2:
                return 1.0
                
            # Simple continuity based on content overlap
            continuity_scores = []
            
            for i in range(len(result.data)-1):
                content1 = set(result.data[i]['content'].lower().split())
                content2 = set(result.data[i+1]['content'].lower().split())
                
                if content1 and content2:
                    overlap = len(content1 & content2) / min(len(content1), len(content2))
                    continuity_scores.append(overlap)
                    
            return np.mean(continuity_scores) if continuity_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error measuring context continuity: {e}")
            return 0.0
            
    async def estimate_user_satisfaction(self, thread_id: str) -> Dict[str, Any]:
        """Estimate user satisfaction based on usage patterns."""
        client = await self.db.client
        
        try:
            # Get thread activity
            result = await client.table('engrams')\
                .select('created_at')\
                .eq('thread_id', thread_id)\
                .order('created_at')\
                .execute()
                
            if not result.data:
                return {'satisfaction_score': 0.5, 'confidence': 'low'}
                
            # Factors for satisfaction
            engram_count = len(result.data)
            
            # Duration of conversation
            times = [datetime.fromisoformat(e['created_at'].replace('Z', '+00:00')) 
                    for e in result.data]
            duration_hours = (times[-1] - times[0]).total_seconds() / 3600 if len(times) > 1 else 0
            
            # Score based on engagement (more engrams = more engaged)
            engagement_score = min(engram_count / 20, 1.0)
            
            # Score based on duration (longer = more satisfied)
            duration_score = min(duration_hours / 2, 1.0)
            
            satisfaction = (engagement_score + duration_score) / 2
            confidence = 'high' if engram_count > 10 else 'medium' if engram_count > 5 else 'low'
            
            return {
                'satisfaction_score': satisfaction,
                'confidence': confidence,
                'engagement_score': engagement_score,
                'duration_score': duration_score
            }
            
        except Exception as e:
            logger.error(f"Error estimating user satisfaction: {e}")
            return {'satisfaction_score': 0.5, 'confidence': 'error'}
    
    async def get_system_wide_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics across all threads."""
        basic_metrics = EngramMetrics()
        
        return {
            'basic_stats': await basic_metrics.get_basic_stats(),
            'retrieval_performance': await self.measure_retrieval_latency('system-wide'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def log_metrics_snapshot(self, thread_id: str) -> Dict[str, Any]:
        """Log a comprehensive metrics snapshot."""
        metrics = {
            'thread_id': thread_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'basic_stats': await EngramMetrics().get_basic_stats(thread_id),
            'memory_health': {
                'diversity_index': await MemoryHealthMetrics().calculate_diversity_index(thread_id),
                'temporal_distribution': await MemoryHealthMetrics().analyze_temporal_distribution(thread_id),
            },
            'cognitive_load': await CognitiveLoadMetrics().get_current_load(thread_id),
            'experience': {
                'context_continuity': await self.measure_context_continuity(thread_id),
                'satisfaction': await self.estimate_user_satisfaction(thread_id)
            }
        }
        
        logger.info(f"Metrics snapshot for thread {thread_id}", extra=metrics)
        return metrics