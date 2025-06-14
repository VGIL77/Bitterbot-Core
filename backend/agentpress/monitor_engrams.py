<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
        
=======
=======
>>>>>>> Stashed changes
#!/usr/bin/env python3
"""
Monitor Engram Memory System Performance.

Run this script to get real-time metrics about your engram memory system.
Usage: python monitor_engrams.py [thread_id]
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from engram_metrics import (
    EngramMetrics,
    MemoryHealthMetrics,
    CognitiveLoadMetrics,
    NeuroscienceMetrics,
    ExperienceMetrics
)
from utils.logger import logger


async def generate_metrics_report(thread_id: Optional[str] = None):
    """Generate a comprehensive metrics report."""
    
    print("\n" + "="*80)
    print("🧠 ENGRAM MEMORY SYSTEM METRICS REPORT")
    print("="*80)
    print(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
    
    if thread_id:
        print(f"Thread ID: {thread_id}")
    else:
        print("Scope: System-wide")
    
    # Initialize metrics
    basic = EngramMetrics()
    health = MemoryHealthMetrics()
    cognitive = CognitiveLoadMetrics()
    neuro = NeuroscienceMetrics()
    experience = ExperienceMetrics()
    
    try:
        # Basic Statistics
        print("\n📊 BASIC STATISTICS")
        print("-" * 40)
        basic_stats = await basic.get_basic_stats(thread_id)
        print(f"Total Engrams: {basic_stats['total_engrams']}")
        print(f"Average Relevance Score: {basic_stats['avg_relevance_score']:.3f}")
        print(f"Average Access Count: {basic_stats['avg_access_count']:.1f}")
        print(f"Average Surprise Score: {basic_stats['avg_surprise_score']:.3f}")
        print(f"Total Tokens Compressed: {basic_stats['total_tokens_compressed']:,}")
        print(f"Total Tokens in Summaries: {basic_stats['total_tokens_in_summaries']:,.0f}")
        
        if basic_stats['total_tokens_compressed'] > 0:
            compression = basic_stats['total_tokens_compressed'] / basic_stats['total_tokens_in_summaries']
            print(f"Compression Ratio: {compression:.2f}:1")
        
        if thread_id and basic_stats['total_engrams'] > 0:
            # Memory Health
            print("\n🏥 MEMORY HEALTH")
            print("-" * 40)
            diversity = await health.calculate_memory_diversity_index(thread_id)
            coherence = await health.calculate_memory_coherence_score(thread_id)
            surprise_accuracy = await health.calculate_surprise_accuracy(thread_id)
            
            print(f"Topic Diversity Index: {diversity:.3f} (0=homogeneous, 1=diverse)")
            print(f"Memory Coherence Score: {coherence:.3f} (0=fragmented, 1=coherent)")
            print(f"Surprise Prediction Accuracy: {surprise_accuracy:.3f} (-1 to 1, higher=better)")
            
            # Cognitive Load
            print("\n🧩 COGNITIVE LOAD MANAGEMENT")
            print("-" * 40)
            compression_ratio = await cognitive.calculate_context_compression_ratio(thread_id)
            retrieval_precision = await cognitive.calculate_retrieval_precision(thread_id)
            coverage = await cognitive.calculate_memory_coverage(thread_id)
            
            print(f"Context Compression Ratio: {compression_ratio:.1f}:1")
            print(f"Retrieval Precision (24h): {retrieval_precision:.1%}")
            print(f"Message Coverage: {coverage['message_coverage']:.1%}")
            print(f"Estimated Token Coverage: {coverage['estimated_token_coverage']:.1%}")
            
            # Neuroscience Metrics
            print("\n🔬 NEUROSCIENCE-INSPIRED METRICS")
            print("-" * 40)
            forgetting_fit = await neuro.calculate_forgetting_curve_fit(thread_id)
            consolidation_waves = await neuro.calculate_consolidation_waves(thread_id)
            
            print(f"Forgetting Curve Fit (R²): {forgetting_fit:.3f} (1=perfect Ebbinghaus curve)")
            print(f"Consolidation Waves Detected: {len(consolidation_waves)}")
            
            if consolidation_waves:
                avg_wave_duration = sum(w['duration_minutes'] for w in consolidation_waves) / len(consolidation_waves)
                avg_engrams_per_wave = sum(w['engram_count'] for w in consolidation_waves) / len(consolidation_waves)
                print(f"  Average Wave Duration: {avg_wave_duration:.1f} minutes")
                print(f"  Average Engrams per Wave: {avg_engrams_per_wave:.1f}")
            
            # Experience Metrics
            print("\n✨ USER EXPERIENCE IMPACT")
            print("-" * 40)
            continuity = await experience.calculate_context_continuity_score(thread_id)
            delight_moments = await experience.calculate_memory_surprise_delight(thread_id)
            
            print(f"Context Continuity Score: {continuity:.3f} (0=amnesia, 1=perfect recall)")
            print(f"Memory Surprise Delight Moments (24h): {delight_moments}")
            
            # Performance Assessment
            print("\n🎯 OVERALL PERFORMANCE ASSESSMENT")
            print("-" * 40)
            
            # Calculate overall health score
            health_score = (
                diversity * 0.15 +
                coherence * 0.20 +
                max(0, surprise_accuracy) * 0.15 +
                min(1, compression_ratio / 10) * 0.20 +
                retrieval_precision * 0.15 +
                continuity * 0.15
            )
            
            print(f"Overall Health Score: {health_score:.1%}")
            
            if health_score >= 0.8:
                assessment = "🟢 EXCELLENT - System performing optimally"
            elif health_score >= 0.6:
                assessment = "🟡 GOOD - Minor optimization opportunities"
            elif health_score >= 0.4:
                assessment = "🟠 FAIR - Consider tuning parameters"
            else:
                assessment = "🔴 NEEDS ATTENTION - Review configuration"
            
            print(f"Assessment: {assessment}")
            
            # Recommendations
            print("\n💡 RECOMMENDATIONS")
            print("-" * 40)
            
            if diversity < 0.3:
                print("- Low topic diversity: Consider more aggressive surprise detection")
            if coherence < 0.5:
                print("- Low coherence: Increase context window for engram creation")
            if compression_ratio < 5:
                print("- Low compression: Review summarization quality")
            if retrieval_precision < 0.5:
                print("- Low retrieval precision: Adjust relevance scoring algorithm")
            if continuity < 0.5:
                print("- Low continuity: Increase max engrams in context")
            
            if health_score >= 0.8:
                print("- System is performing well! No major changes needed.")
    
    except Exception as e:
        logger.error(f"Error generating metrics report: {e}")
        print(f"\n❌ Error generating report: {e}")
    
    print("\n" + "="*80 + "\n")


async def monitor_realtime(thread_id: Optional[str] = None):
    """Monitor metrics in real-time with periodic updates."""
    
    print("\n🔄 Starting real-time monitoring (Ctrl+C to stop)...")
    print("Updates every 60 seconds\n")
    
    try:
        while True:
            await generate_metrics_report(thread_id)
            await asyncio.sleep(60)  # Update every minute
    except KeyboardInterrupt:
        print("\n✋ Monitoring stopped.")


async def main():
    """Main entry point."""
    
    if len(sys.argv) > 2 and sys.argv[1] == "--realtime":
        thread_id = sys.argv[2] if len(sys.argv) > 2 else None
        await monitor_realtime(thread_id)
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        print("\nOptions:")
        print("  python monitor_engrams.py                    # System-wide report")
        print("  python monitor_engrams.py THREAD_ID          # Single thread report")
        print("  python monitor_engrams.py --realtime         # Real-time monitoring")
        print("  python monitor_engrams.py --realtime THREAD_ID  # Real-time for thread")
    else:
        thread_id = sys.argv[1] if len(sys.argv) > 1 else None
        await generate_metrics_report(thread_id)

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

if __name__ == "__main__":
    asyncio.run(main())