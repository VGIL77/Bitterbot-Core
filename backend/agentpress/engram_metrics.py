"""
Metrics and Analytics for Engram Memory System.

This module provides comprehensive metrics to assess the effectiveness
of the neuroscience-inspired memory consolidation system.
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np

from services.supabase import DBConnection
from utils.logger import logger


class EngramMetrics:
    """Core metrics for the engram memory system."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def get_basic_stats(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Get basic statistics about engrams."""
        client = await self.db.client
        
        query = client.table('engrams').select('*')
        if thread_id:
            query = query.eq('thread_id', thread_id)
            
        result = await query.execute()
        engrams = result.data
        
        if not engrams:
            return {
                'total_engrams': 0,
                'avg_relevance_score': 0,
                'avg_access_count': 0,
                'avg_surprise_score': 0
            }
            
        return {
            'total_engrams': len(engrams),
            'avg_relevance_score': sum(e['relevance_score'] for e in engrams) / len(engrams),
            'avg_access_count': sum(e['access_count'] for e in engrams) / len(engrams),
            'avg_surprise_score': sum(e['surprise_score'] for e in engrams) / len(engrams),
            'total_tokens_compressed': sum(e['token_count'] for e in engrams),
            'total_tokens_in_summaries': sum(len(e['content'].split()) * 1.3 for e in engrams)  # Rough estimate
        }


class MemoryHealthMetrics:
    """Track the overall health of the memory system."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_memory_diversity_index(self, thread_id: str) -> float:
        """
        Shannon diversity index of engram topics.
        Higher = more diverse conversation coverage.
        H = -Σ(pi * log(pi)) where pi is proportion of each topic
        """
        client = await self.db.client
        result = await client.table('engrams').select('metadata').eq('thread_id', thread_id).execute()
        
        if not result.data:
            return 0.0
            
        # Count topic frequencies
        topic_counts = Counter()
        for engram in result.data:
            topics = engram['metadata'].get('topics', [])
            topic_counts.update(topics)
            
        if not topic_counts:
            return 0.0
            
        # Calculate Shannon diversity
        total = sum(topic_counts.values())
        diversity = 0.0
        
        for count in topic_counts.values():
            if count > 0:
                p = count / total
                diversity -= p * math.log(p)
                
        # Normalize to 0-1 by dividing by log(num_topics)
        if len(topic_counts) > 1:
            diversity = diversity / math.log(len(topic_counts))
            
        return diversity
        
    async def calculate_memory_coherence_score(self, thread_id: str) -> float:
        """
        Measure semantic flow between consecutive engrams.
        Uses simple keyword overlap as a proxy for semantic similarity.
        """
        client = await self.db.client
        result = await client.table('engrams').select('content, created_at').eq(
            'thread_id', thread_id
        ).order('created_at').execute()
        
        if len(result.data) < 2:
            return 1.0  # Perfect coherence if only one engram
            
        coherence_scores = []
        
        for i in range(1, len(result.data)):
            prev_content = set(result.data[i-1]['content'].lower().split())
            curr_content = set(result.data[i]['content'].lower().split())
            
            # Jaccard similarity
            intersection = len(prev_content & curr_content)
            union = len(prev_content | curr_content)
            
            if union > 0:
                coherence_scores.append(intersection / union)
                
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        
    async def calculate_surprise_accuracy(self, thread_id: str) -> float:
        """
        Correlation between surprise scores and actual access patterns.
        High correlation = we're good at identifying important moments.
        """
        client = await self.db.client
        result = await client.table('engrams').select(
            'surprise_score, access_count'
        ).eq('thread_id', thread_id).execute()
        
        if len(result.data) < 2:
            return 0.0
            
        surprise_scores = [e['surprise_score'] for e in result.data]
        access_counts = [e['access_count'] for e in result.data]
        
        # Calculate Pearson correlation
        if len(set(surprise_scores)) == 1 or len(set(access_counts)) == 1:
            return 0.0  # No variance in one variable
            
        n = len(surprise_scores)
        sum_x = sum(surprise_scores)
        sum_y = sum(access_counts)
        sum_xy = sum(x * y for x, y in zip(surprise_scores, access_counts))
        sum_x2 = sum(x * x for x in surprise_scores)
        sum_y2 = sum(y * y for y in access_counts)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator


class CognitiveLoadMetrics:
    """Measure how well we're managing cognitive load."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_context_compression_ratio(self, thread_id: str) -> float:
        """
        Ratio of full conversation tokens to engram summary tokens.
        Higher = better compression.
        """
        client = await self.db.client
        
        # Get total tokens from engrams
        engrams_result = await client.table('engrams').select(
            'token_count, content'
        ).eq('thread_id', thread_id).execute()
        
        if not engrams_result.data:
            return 1.0
            
        original_tokens = sum(e['token_count'] for e in engrams_result.data)
        # Estimate summary tokens (rough: 1.3 tokens per word)
        summary_tokens = sum(len(e['content'].split()) * 1.3 for e in engrams_result.data)
        
        if summary_tokens == 0:
            return float('inf')
            
        return original_tokens / summary_tokens
        
    async def calculate_retrieval_precision(self, thread_id: str, window_hours: int = 24) -> float:
        """
        Of recently retrieved engrams, what % were accessed again?
        Indicates if our retrieval is actually useful.
        """
        client = await self.db.client
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        
        result = await client.table('engrams').select(
            'access_count, last_accessed'
        ).eq('thread_id', thread_id).gt('last_accessed', cutoff_time.isoformat()).execute()
        
        if not result.data:
            return 0.0
            
        # Engrams accessed more than once are considered "useful"
        useful_retrievals = sum(1 for e in result.data if e['access_count'] > 1)
        total_retrievals = len(result.data)
        
        return useful_retrievals / total_retrievals if total_retrievals > 0 else 0.0
        
    async def calculate_memory_coverage(self, thread_id: str) -> Dict[str, float]:
        """
        What % of conversation is covered by engrams?
        Returns coverage by message count and token count.
        """
        client = await self.db.client
        
        # Get message count from thread
        messages_result = await client.table('messages').select(
            'message_id'
        ).eq('thread_id', thread_id).in_('type', ['user', 'assistant']).execute()
        
        # Get engram coverage
        engrams_result = await client.table('engrams').select(
            'message_range'
        ).eq('thread_id', thread_id).execute()
        
        if not messages_result.data:
            return {'message_coverage': 0.0, 'estimated_token_coverage': 0.0}
            
        total_messages = len(messages_result.data)
        covered_messages = set()
        
        for engram in engrams_result.data:
            msg_range = engram['message_range']
            if msg_range and 'start' in msg_range and 'end' in msg_range:
                # This is simplified - in reality, you'd enumerate the actual message IDs
                covered_messages.add(msg_range['start'])
                covered_messages.add(msg_range['end'])
                
        message_coverage = len(covered_messages) / total_messages if total_messages > 0 else 0.0
        
        return {
            'message_coverage': message_coverage,
            'estimated_token_coverage': message_coverage * 0.8  # Assume 80% token coverage
        }


class NeuroscienceMetrics:
    """Metrics inspired by neuroscience research."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_hebbian_strength(self, engram_id: str) -> float:
        """
        'Neurons that fire together, wire together'
        Measure how often this engram is retrieved with others.
        """
        client = await self.db.client
        
        # Get the engram's thread and access times
        engram_result = await client.table('engrams').select(
            'thread_id, last_accessed'
        ).eq('id', engram_id).execute()
        
        if not engram_result.data:
            return 0.0
            
        thread_id = engram_result.data[0]['thread_id']
        target_time = datetime.fromisoformat(engram_result.data[0]['last_accessed'])
        
        # Find other engrams accessed within 5 minutes
        time_window = timedelta(minutes=5)
        start_time = (target_time - time_window).isoformat()
        end_time = (target_time + time_window).isoformat()
        
        coactivated_result = await client.table('engrams').select('id').eq(
            'thread_id', thread_id
        ).neq('id', engram_id).gte('last_accessed', start_time).lte(
            'last_accessed', end_time
        ).execute()
        
        # Hebbian strength = number of co-activations
        return len(coactivated_result.data)
        
    async def calculate_forgetting_curve_fit(self, thread_id: str) -> float:
        """
        How well does our decay match Ebbinghaus forgetting curve?
        Returns R² value of exponential decay fit.
        """
        client = await self.db.client
        result = await client.table('engrams').select(
            'created_at, last_accessed, relevance_score'
        ).eq('thread_id', thread_id).execute()
        
        if len(result.data) < 5:  # Need enough data points
            return 0.0
            
        # Calculate days since creation and relevance scores
        data_points = []
        now = datetime.now(timezone.utc)
        
        for engram in result.data:
            created = datetime.fromisoformat(engram['created_at'])
            days_old = (now - created).days
            if days_old > 0:
                data_points.append((days_old, engram['relevance_score']))
                
        if len(data_points) < 3:
            return 0.0
            
        # Simple R² calculation for exponential decay
        # Expected: relevance = initial * (decay_rate ^ days)
        # Log transform: log(relevance) = log(initial) + days * log(decay_rate)
        
        x_values = [p[0] for p in data_points]
        y_values = [math.log(p[1]) if p[1] > 0 else -10 for p in data_points]
        
        # Calculate R²
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        # Slope and intercept
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R²
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        
        if ss_tot == 0:
            return 0.0
            
        return 1 - (ss_res / ss_tot)
        
    async def calculate_consolidation_waves(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Identify 'sleep-like' consolidation patterns.
        Burst of engram creation followed by quiet periods.
        """
        client = await self.db.client
        result = await client.table('engrams').select(
            'created_at'
        ).eq('thread_id', thread_id).order('created_at').execute()
        
        if len(result.data) < 2:
            return []
            
        # Calculate time gaps between engrams
        waves = []
        current_wave = {'start': result.data[0]['created_at'], 'engram_count': 1}
        
        for i in range(1, len(result.data)):
            prev_time = datetime.fromisoformat(result.data[i-1]['created_at'])
            curr_time = datetime.fromisoformat(result.data[i]['created_at'])
            gap_minutes = (curr_time - prev_time).total_seconds() / 60
            
            if gap_minutes > 30:  # 30+ minute gap = new wave
                current_wave['end'] = result.data[i-1]['created_at']
                current_wave['duration_minutes'] = (
                    datetime.fromisoformat(current_wave['end']) - 
                    datetime.fromisoformat(current_wave['start'])
                ).total_seconds() / 60
                waves.append(current_wave)
                current_wave = {'start': result.data[i]['created_at'], 'engram_count': 1}
            else:
                current_wave['engram_count'] += 1
                
        # Add final wave
        current_wave['end'] = result.data[-1]['created_at']
        current_wave['duration_minutes'] = (
            datetime.fromisoformat(current_wave['end']) - 
            datetime.fromisoformat(current_wave['start'])
        ).total_seconds() / 60
        waves.append(current_wave)
        
        return waves


class ExperienceMetrics:
    """Measure actual impact on user experience."""
    
    def __init__(self):
        self.db = DBConnection()
        
    async def calculate_context_continuity_score(self, thread_id: str) -> float:
        """
        How well does the AI maintain context across long conversations?
        Based on engram retrieval patterns.
        """
        client = await self.db.client
        
        # Get engrams ordered by creation
        result = await client.table('engrams').select(
            'id, created_at, access_count'
        ).eq('thread_id', thread_id).order('created_at').execute()
        
        if len(result.data) < 2:
            return 1.0
            
        # Calculate "reach-back" score
        # How often do we access older engrams?
        total_accesses = sum(e['access_count'] for e in result.data)
        if total_accesses == 0:
            return 0.0
            
        # Weight by age - accessing older memories shows continuity
        weighted_score = 0.0
        for i, engram in enumerate(result.data):
            age_weight = (i + 1) / len(result.data)  # Older = higher weight
            weighted_score += engram['access_count'] * age_weight
            
        # Normalize
        max_possible = total_accesses * 0.5  # Average position weight
        return weighted_score / max_possible if max_possible > 0 else 0.0
        
    async def calculate_memory_surprise_delight(self, thread_id: str) -> int:
        """
        Count 'wow, you remembered that!' moments.
        High-relevance old engrams that get accessed.
        """
        client = await self.db.client
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Find old engrams (>24h) with high relevance that were recently accessed
        result = await client.table('engrams').select('*').eq(
            'thread_id', thread_id
        ).lt('created_at', cutoff_time.isoformat()).gt(
            'relevance_score', 2.0
        ).gt('access_count', 0).execute()
        
        # Count those accessed in last 24 hours
        delight_moments = 0
        for engram in result.data:
            last_accessed = datetime.fromisoformat(engram['last_accessed'])
            if last_accessed > cutoff_time:
                delight_moments += 1
                
        return delight_moments
        
    async def log_metrics_snapshot(self, thread_id: str):
        """
        Log a comprehensive metrics snapshot for analysis.
        """
        # Gather all metrics
        basic_metrics = EngramMetrics()
        health_metrics = MemoryHealthMetrics()
        cognitive_metrics = CognitiveLoadMetrics()
        neuro_metrics = NeuroscienceMetrics()
        experience_metrics = ExperienceMetrics()
        
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "thread_id": thread_id,
            "basic_stats": await basic_metrics.get_basic_stats(thread_id),
            "memory_health": {
                "diversity_index": await health_metrics.calculate_memory_diversity_index(thread_id),
                "coherence_score": await health_metrics.calculate_memory_coherence_score(thread_id),
                "surprise_accuracy": await health_metrics.calculate_surprise_accuracy(thread_id)
            },
            "cognitive_load": {
                "compression_ratio": await cognitive_metrics.calculate_context_compression_ratio(thread_id),
                "retrieval_precision": await cognitive_metrics.calculate_retrieval_precision(thread_id),
                "memory_coverage": await cognitive_metrics.calculate_memory_coverage(thread_id)
            },
            "neuroscience": {
                "forgetting_curve_fit": await neuro_metrics.calculate_forgetting_curve_fit(thread_id),
                "consolidation_waves": await neuro_metrics.calculate_consolidation_waves(thread_id)
            },
            "experience": {
                "context_continuity": await experience_metrics.calculate_context_continuity_score(thread_id),
                "surprise_delight_moments": await experience_metrics.calculate_memory_surprise_delight(thread_id)
            }
        }
        
        logger.info("ENGRAM_METRICS_SNAPSHOT", extra={
            "metrics_type": "comprehensive_snapshot",
            "thread_id": thread_id,
            "metrics_data": snapshot
        })
        
        return snapshot


# Convenience functions for regular metric logging
async def log_engram_created(engram_id: str, thread_id: str, trigger: str, 
                           message_count: int, token_count: int, 
                           surprise_score: float, topics: List[str],
                           compression_ratio: float):
    """Log engram creation with all relevant metrics."""
    logger.info("ENGRAM_METRICS", extra={
        "event_type": "engram_created",
        "thread_id": thread_id,
        "engram_id": engram_id,
        "trigger": trigger,  # "token_threshold", "surprise", "forced"
        "message_count": message_count,
        "token_count": token_count,
        "surprise_score": surprise_score,
        "topics": topics,
        "compression_ratio": compression_ratio,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def log_engram_retrieved(thread_id: str, query_tokens: int,
                             retrieved_engrams: List[Dict[str, Any]],
                             total_available: int, retrieval_time_ms: float):
    """Log engram retrieval with performance metrics."""
    logger.info("ENGRAM_METRICS", extra={
        "event_type": "engram_retrieved",
        "thread_id": thread_id,
        "query_tokens": query_tokens,
        "retrieved_count": len(retrieved_engrams),
        "retrieved_engram_ids": [e['id'] for e in retrieved_engrams],
        "relevance_scores": [e['relevance_score'] for e in retrieved_engrams],
        "total_engrams_available": total_available,
        "retrieval_time_ms": retrieval_time_ms,
        "avg_age_hours": sum(
            (datetime.now(timezone.utc) - datetime.fromisoformat(e['created_at'])).total_seconds() / 3600
            for e in retrieved_engrams
        ) / len(retrieved_engrams) if retrieved_engrams else 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })