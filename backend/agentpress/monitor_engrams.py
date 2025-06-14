"""
Engram Memory System Monitoring Script.

Run this periodically to generate metrics reports and identify trends.

Usage:
    python monitor_engrams.py [--thread-id THREAD_ID] [--format json|markdown]
"""

import asyncio
import argparse
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from engram_metrics import (
    EngramMetrics, MemoryHealthMetrics, CognitiveLoadMetrics,
    NeuroscienceMetrics, ExperienceMetrics
)
from services.supabase import DBConnection
from utils.logger import logger


class EngramMonitor:
    """Monitor and report on engram system performance."""
    
    def __init__(self):
        self.db = DBConnection()
        self.basic_metrics = EngramMetrics()
        self.health_metrics = MemoryHealthMetrics()
        self.cognitive_metrics = CognitiveLoadMetrics()
        self.neuro_metrics = NeuroscienceMetrics()
        self.experience_metrics = ExperienceMetrics()
        
    async def generate_report(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "thread_id": thread_id or "all_threads",
            "report_type": "thread_specific" if thread_id else "system_wide"
        }
        
        # Basic statistics
        report["basic_stats"] = await self.basic_metrics.get_basic_stats(thread_id)
        
        if thread_id:
            # Thread-specific metrics
            report["memory_health"] = {
                "diversity": await self.health_metrics.calculate_diversity_index(thread_id),
                "temporal_distribution": await self.health_metrics.analyze_temporal_distribution(thread_id),
                "decay_analysis": await self.health_metrics.analyze_decay_patterns(thread_id)
            }
            
            report["cognitive_load"] = await self.cognitive_metrics.get_current_load(thread_id)
            
            report["neuroscience"] = {
                "hebbian_strength": await self.neuro_metrics.calculate_hebbian_strength(thread_id),
                "surprise_effectiveness": await self.neuro_metrics.analyze_surprise_effectiveness(thread_id),
                "consolidation_patterns": await self.neuro_metrics.detect_consolidation_patterns(thread_id)
            }
            
            report["experience"] = {
                "retrieval_latency": await self.experience_metrics.measure_retrieval_latency(thread_id),
                "context_continuity": await self.experience_metrics.measure_context_continuity(thread_id),
                "user_satisfaction": await self.experience_metrics.estimate_user_satisfaction(thread_id)
            }
        else:
            # System-wide metrics
            report["system_health"] = await self._get_system_health()
            report["usage_patterns"] = await self._get_usage_patterns()
            report["performance_trends"] = await self._get_performance_trends()
        
        return report
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        client = await self.db.client
        
        # Total engrams
        result = await client.table('engrams').select('id', count='exact').execute()
        total_engrams = result.count
        
        # Active threads (last 24h)
        one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        result = await client.table('engrams').select('thread_id') \
            .gte('created_at', one_day_ago).execute()
        active_threads = len(set(row['thread_id'] for row in result.data))
        
        # Average consolidation rate
        result = await client.rpc('get_system_wide_stats').execute()
        stats = result.data[0] if result.data else {}
        
        return {
            "total_engrams": total_engrams,
            "active_threads_24h": active_threads,
            "avg_consolidation_rate": stats.get('avg_consolidation_rate', 0),
            "avg_relevance_score": stats.get('avg_relevance_score', 0),
            "memory_efficiency": stats.get('compression_ratio', 0)
        }
    
    async def _get_usage_patterns(self) -> Dict[str, Any]:
        """Analyze system-wide usage patterns."""
        client = await self.db.client
        
        # Peak hours analysis
        result = await client.rpc('analyze_usage_by_hour').execute()
        peak_hours = result.data if result.data else []
        
        # Most active threads
        result = await client.table('engrams').select('thread_id') \
            .order('created_at', desc=True).limit(1000).execute()
        
        thread_counts = {}
        for row in result.data:
            thread_id = row['thread_id']
            thread_counts[thread_id] = thread_counts.get(thread_id, 0) + 1
        
        top_threads = sorted(thread_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "peak_hours": peak_hours,
            "top_threads": [{"thread_id": t[0], "engram_count": t[1]} for t in top_threads],
            "avg_engrams_per_thread": sum(thread_counts.values()) / len(thread_counts) if thread_counts else 0
        }
    
    async def _get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        # This would typically involve more sophisticated time-series analysis
        # For now, returning placeholder data
        return {
            "consolidation_efficiency_trend": "improving",
            "retrieval_accuracy_trend": "stable",
            "memory_footprint_trend": "optimizing"
        }
    
    def format_report(self, report: Dict[str, Any], format: str = "markdown") -> str:
        """Format report for output."""
        if format == "json":
            return json.dumps(report, indent=2)
        
        # Markdown format
        lines = [
            "# Engram System Metrics Report",
            f"\n**Generated**: {report['generated_at']}",
            f"**Type**: {report['report_type']}",
        ]
        
        if report.get('thread_id') != 'all_threads':
            lines.append(f"**Thread**: {report['thread_id']}")
        
        lines.append("\n## Basic Statistics")
        if 'basic_stats' in report:
            stats = report['basic_stats']
            lines.extend([
                f"- Total Engrams: {stats.get('total_engrams', 0)}",
                f"- Average Relevance: {stats.get('avg_relevance_score', 0):.3f}",
                f"- Average Surprise: {stats.get('avg_surprise_score', 0):.3f}",
                f"- Compression Ratio: {stats.get('compression_ratio', 0):.2f}x"
            ])
        
        if 'memory_health' in report:
            lines.append("\n## Memory Health")
            health = report['memory_health']
            lines.extend([
                f"- Diversity Index: {health.get('diversity', 0):.3f}",
                f"- Temporal Distribution: {health.get('temporal_distribution', 'unknown')}",
                f"- Decay Pattern: {health.get('decay_analysis', {}).get('pattern', 'unknown')}"
            ])
        
        if 'cognitive_load' in report:
            lines.append("\n## Cognitive Load")
            load = report['cognitive_load']
            lines.extend([
                f"- Current Load: {load.get('current_load', 0):.2%}",
                f"- Status: {load.get('status', 'unknown')}"
            ])
        
        if 'system_health' in report:
            lines.append("\n## System Health")
            health = report['system_health']
            lines.extend([
                f"- Total Engrams: {health.get('total_engrams', 0):,}",
                f"- Active Threads (24h): {health.get('active_threads_24h', 0)}",
                f"- Avg Consolidation Rate: {health.get('avg_consolidation_rate', 0):.2f}/min",
                f"- Memory Efficiency: {health.get('memory_efficiency', 0):.2f}x"
            ])
        
        return "\n".join(lines)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor Engram Memory System")
    parser.add_argument('--thread-id', help='Specific thread ID to analyze')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown',
                       help='Output format')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously, updating every 5 minutes')
    
    args = parser.parse_args()
    
    monitor = EngramMonitor()
    
    if args.continuous:
        logger.info("Starting continuous monitoring...")
        while True:
            report = await monitor.generate_report(args.thread_id)
            print("\n" + "="*80)
            print(monitor.format_report(report, args.format))
            await asyncio.sleep(300)  # 5 minutes
    else:
        report = await monitor.generate_report(args.thread_id)
        print(monitor.format_report(report, args.format))


if __name__ == "__main__":
    asyncio.run(main())