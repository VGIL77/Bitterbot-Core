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
                "diversity_index": await self.health_metrics.calculate_memory_diversity_index(thread_id),
                "coherence_score": await self.health_metrics.calculate_memory_coherence_score(thread_id),
                "surprise_accuracy": await self.health_metrics.calculate_surprise_accuracy(thread_id)
            }
            
            report["cognitive_load"] = {
                "compression_ratio": await self.cognitive_metrics.calculate_context_compression_ratio(thread_id),
                "retrieval_precision_24h": await self.cognitive_metrics.calculate_retrieval_precision(thread_id, 24),
                "memory_coverage": await self.cognitive_metrics.calculate_memory_coverage(thread_id)
            }
            
            report["neuroscience"] = {
                "forgetting_curve_fit": await self.neuro_metrics.calculate_forgetting_curve_fit(thread_id),
                "consolidation_waves": await self.neuro_metrics.calculate_consolidation_waves(thread_id)
            }
            
            report["experience"] = {
                "context_continuity": await self.experience_metrics.calculate_context_continuity_score(thread_id),
                "surprise_delight_moments": await self.experience_metrics.calculate_memory_surprise_delight(thread_id)
            }
        else:
            # System-wide metrics
            report["system_health"] = await self._calculate_system_health()
            report["usage_patterns"] = await self._calculate_usage_patterns()
            
        # Generate insights
        report["insights"] = self._generate_insights(report)
        
        return report
        
    async def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate system-wide health metrics."""
        client = await self.db.client
        
        # Get all engrams from last 7 days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        result = await client.table('engrams').select('*').gt('created_at', cutoff).execute()
        
        if not result.data:
            return {"status": "no_recent_data"}
            
        engrams = result.data
        
        # Calculate health indicators
        total_engrams = len(engrams)
        avg_access = sum(e['access_count'] for e in engrams) / total_engrams
        high_relevance = sum(1 for e in engrams if e['relevance_score'] > 5.0)
        stale_engrams = sum(1 for e in engrams if e['access_count'] == 0)
        
        return {
            "total_engrams_7d": total_engrams,
            "avg_access_per_engram": avg_access,
            "high_relevance_percentage": (high_relevance / total_engrams) * 100,
            "stale_percentage": (stale_engrams / total_engrams) * 100,
            "health_score": self._calculate_health_score(avg_access, stale_engrams / total_engrams)
        }
        
    async def _calculate_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns across the system."""
        client = await self.db.client
        
        # Get hourly creation patterns
        result = await client.table('engrams').select('created_at').execute()
        
        if not result.data:
            return {"status": "no_data"}
            
        # Analyze creation patterns
        hourly_counts = [0] * 24
        daily_counts = defaultdict(int)
        
        for engram in result.data:
            created = datetime.fromisoformat(engram['created_at'])
            hourly_counts[created.hour] += 1
            daily_counts[created.strftime('%A')] += 1
            
        # Find peak hours
        peak_hour = hourly_counts.index(max(hourly_counts))
        
        return {
            "peak_hour": f"{peak_hour}:00-{peak_hour+1}:00 UTC",
            "hourly_distribution": hourly_counts,
            "daily_distribution": dict(daily_counts),
            "busiest_day": max(daily_counts, key=daily_counts.get) if daily_counts else "N/A"
        }
        
    def _calculate_health_score(self, avg_access: float, stale_ratio: float) -> float:
        """Calculate overall health score (0-100)."""
        # Higher access is good (weight: 60%)
        access_score = min(avg_access * 20, 60)  # Cap at 60
        
        # Lower stale ratio is good (weight: 40%)
        freshness_score = (1 - stale_ratio) * 40
        
        return access_score + freshness_score
        
    def _generate_insights(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from metrics."""
        insights = {
            "recommendations": [],
            "warnings": [],
            "achievements": []
        }
        
        # Check compression ratio
        if "cognitive_load" in report:
            compression = report["cognitive_load"].get("compression_ratio", 0)
            if compression > 10:
                insights["achievements"].append(
                    f"Excellent compression ratio ({compression:.1f}:1) - "
                    "Engrams are effectively condensing information"
                )
            elif compression < 3:
                insights["warnings"].append(
                    f"Low compression ratio ({compression:.1f}:1) - "
                    "Consider adjusting summary generation"
                )
                
        # Check memory diversity
        if "memory_health" in report:
            diversity = report["memory_health"].get("diversity_index", 0)
            if diversity < 0.3:
                insights["recommendations"].append(
                    "Low topic diversity - Conversation may be too focused. "
                    "Consider exploring related topics."
                )
            elif diversity > 0.8:
                insights["achievements"].append(
                    "High topic diversity - Conversation covers many areas effectively"
                )
                
        # Check retrieval precision
        if "cognitive_load" in report:
            precision = report["cognitive_load"].get("retrieval_precision_24h", 0)
            if precision < 0.5:
                insights["warnings"].append(
                    f"Low retrieval precision ({precision:.1%}) - "
                    "Many retrieved engrams aren't being reused"
                )
                
        # Check surprise accuracy
        if "memory_health" in report:
            surprise_accuracy = report["memory_health"].get("surprise_accuracy", 0)
            if abs(surprise_accuracy) > 0.7:
                insights["achievements"].append(
                    "Strong correlation between surprise detection and usage - "
                    "System is identifying important moments well"
                )
                
        # System-wide insights
        if "system_health" in report:
            health = report["system_health"]
            if health.get("stale_percentage", 0) > 30:
                insights["recommendations"].append(
                    "High percentage of unused engrams - "
                    "Consider adjusting creation threshold or improving retrieval"
                )
                
        return insights
        
    def format_markdown(self, report: Dict[str, Any]) -> str:
        """Format report as markdown."""
        md = [
            "# 🧠 Engram Memory System Report",
            f"\n**Generated**: {report['generated_at']}",
            f"**Scope**: {report['report_type']}",
        ]
        
        if report["thread_id"] != "all_threads":
            md.append(f"**Thread ID**: {report['thread_id']}")
            
        # Basic stats
        if "basic_stats" in report:
            stats = report["basic_stats"]
            md.extend([
                "\n## 📊 Basic Statistics",
                f"- **Total Engrams**: {stats.get('total_engrams', 0)}",
                f"- **Average Relevance**: {stats.get('avg_relevance_score', 0):.2f}",
                f"- **Average Access Count**: {stats.get('avg_access_count', 0):.1f}",
                f"- **Compression Ratio**: {stats.get('total_tokens_compressed', 0) / max(stats.get('total_tokens_in_summaries', 1), 1):.1f}:1"
            ])
            
        # Memory health
        if "memory_health" in report:
            health = report["memory_health"]
            md.extend([
                "\n## 🏥 Memory Health",
                f"- **Topic Diversity**: {health.get('diversity_index', 0):.2f} (0-1 scale)",
                f"- **Coherence Score**: {health.get('coherence_score', 0):.2f}",
                f"- **Surprise Accuracy**: {health.get('surprise_accuracy', 0):.2f} correlation"
            ])
            
        # Cognitive load
        if "cognitive_load" in report:
            cognitive = report["cognitive_load"]
            coverage = cognitive.get("memory_coverage", {})
            md.extend([
                "\n## 🧩 Cognitive Load Management",
                f"- **Compression Ratio**: {cognitive.get('compression_ratio', 0):.1f}:1",
                f"- **Retrieval Precision (24h)**: {cognitive.get('retrieval_precision_24h', 0):.1%}",
                f"- **Message Coverage**: {coverage.get('message_coverage', 0):.1%}"
            ])
            
        # Neuroscience metrics
        if "neuroscience" in report:
            neuro = report["neuroscience"]
            waves = neuro.get("consolidation_waves", [])
            md.extend([
                "\n## 🔬 Neuroscience-Inspired Metrics",
                f"- **Forgetting Curve Fit (R²)**: {neuro.get('forgetting_curve_fit', 0):.3f}",
                f"- **Consolidation Waves**: {len(waves)} detected"
            ])
            
        # Experience
        if "experience" in report:
            exp = report["experience"]
            md.extend([
                "\n## ✨ User Experience Impact",
                f"- **Context Continuity**: {exp.get('context_continuity', 0):.2f}",
                f"- **Surprise & Delight Moments**: {exp.get('surprise_delight_moments', 0)}"
            ])
            
        # System health
        if "system_health" in report:
            health = report["system_health"]
            if health.get("status") != "no_recent_data":
                md.extend([
                    "\n## 💪 System Health",
                    f"- **Health Score**: {health.get('health_score', 0):.1f}/100",
                    f"- **7-Day Engrams**: {health.get('total_engrams_7d', 0)}",
                    f"- **Avg Access/Engram**: {health.get('avg_access_per_engram', 0):.1f}",
                    f"- **High Relevance**: {health.get('high_relevance_percentage', 0):.1f}%",
                    f"- **Stale Engrams**: {health.get('stale_percentage', 0):.1f}%"
                ])
                
        # Insights
        if "insights" in report:
            insights = report["insights"]
            md.append("\n## 💡 Insights & Recommendations")
            
            if insights["achievements"]:
                md.append("\n### 🏆 Achievements")
                for achievement in insights["achievements"]:
                    md.append(f"- ✅ {achievement}")
                    
            if insights["recommendations"]:
                md.append("\n### 📋 Recommendations")
                for rec in insights["recommendations"]:
                    md.append(f"- 💡 {rec}")
                    
            if insights["warnings"]:
                md.append("\n### ⚠️ Warnings")
                for warning in insights["warnings"]:
                    md.append(f"- ⚠️ {warning}")
                    
        return "\n".join(md)


async def main():
    """Main entry point for monitoring script."""
    parser = argparse.ArgumentParser(description="Monitor Engram Memory System")
    parser.add_argument("--thread-id", help="Specific thread ID to analyze")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown",
                       help="Output format (default: markdown)")
    parser.add_argument("--save", help="Save report to file")
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = EngramMonitor()
    
    try:
        # Generate report
        print("🧠 Generating Engram Memory System Report...")
        report = await monitor.generate_report(args.thread_id)
        
        # Format output
        if args.format == "json":
            output = json.dumps(report, indent=2)
        else:
            output = monitor.format_markdown(report)
            
        # Display or save
        if args.save:
            with open(args.save, 'w') as f:
                f.write(output)
            print(f"✅ Report saved to: {args.save}")
        else:
            print(output)
            
        # Log snapshot for system monitoring
        if args.thread_id:
            experience_metrics = ExperienceMetrics()
            await experience_metrics.log_metrics_snapshot(args.thread_id)
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        print(f"❌ Error: {e}")
        

if __name__ == "__main__":
    asyncio.run(main())