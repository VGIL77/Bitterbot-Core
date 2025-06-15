"""
Metrics Collector for BitterBot AGI Platform

This module collects and aggregates metrics from all platform components.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import psutil
import time
from prometheus_client import Counter, Gauge, Histogram, Summary


@dataclass
class MetricSnapshot:
    """Represents a snapshot of system metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    worker_count: int
    service_health: Dict[str, str]


class MetricsCollector:
    """
    Collects and aggregates metrics across the platform.
    
    Features:
    - System resource monitoring
    - Task execution metrics
    - Service health tracking
    - Performance profiling
    """
    
    def __init__(self):
        # Prometheus metrics
        self.task_counter = Counter('bitterbot_tasks_total', 
                                  'Total number of tasks', 
                                  ['status', 'task_type'])
        self.worker_gauge = Gauge('bitterbot_workers_active', 
                                'Number of active workers')
        self.cpu_usage_gauge = Gauge('bitterbot_cpu_usage_percent', 
                                   'CPU usage percentage')
        self.memory_usage_gauge = Gauge('bitterbot_memory_usage_bytes', 
                                      'Memory usage in bytes')
        self.task_duration_histogram = Histogram('bitterbot_task_duration_seconds',
                                               'Task execution duration',
                                               ['task_type'])
        
        self.metrics_history: List[MetricSnapshot] = []
        self.collection_interval = 10  # seconds
        
    async def collect_system_metrics(self) -> MetricSnapshot:
        """
        Collect current system metrics.
        
        Returns:
            Metric snapshot
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage_gauge.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage_gauge.set(memory.used)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        }
        
        # Create snapshot
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            network_io=network_io,
            active_tasks=0,  # TODO: Get from task manager
            completed_tasks=0,  # TODO: Get from task manager
            failed_tasks=0,  # TODO: Get from task manager
            worker_count=0,  # TODO: Get from worker pool
            service_health={}  # TODO: Get from health checker
        )
        
        self.metrics_history.append(snapshot)
        
        # Keep only last hour of history
        cutoff_time = datetime.now().timestamp() - 3600
        self.metrics_history = [m for m in self.metrics_history 
                              if m.timestamp.timestamp() > cutoff_time]
        
        return snapshot
        
    async def record_task_completion(self, 
                                   task_type: str,
                                   duration: float,
                                   success: bool) -> None:
        """
        Record task completion metrics.
        
        Args:
            task_type: Type of task
            duration: Task duration in seconds
            success: Whether task succeeded
        """
        status = "success" if success else "failure"
        self.task_counter.labels(status=status, task_type=task_type).inc()
        self.task_duration_histogram.labels(task_type=task_type).observe(duration)
        
    async def update_worker_count(self, count: int) -> None:
        """
        Update active worker count.
        
        Args:
            count: Number of active workers
        """
        self.worker_gauge.set(count)
        
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics summary.
        
        Returns:
            Metrics dictionary
        """
        latest = await self.collect_system_metrics()
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "system": {
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage,
                "disk_usage": latest.disk_usage,
                "network_io": latest.network_io
            },
            "tasks": {
                "active": latest.active_tasks,
                "completed": latest.completed_tasks,
                "failed": latest.failed_tasks
            },
            "workers": {
                "count": latest.worker_count
            },
            "services": latest.service_health
        }
        
    async def get_metrics_history(self, 
                                duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Get metrics history.
        
        Args:
            duration_minutes: History duration in minutes
            
        Returns:
            List of metric snapshots
        """
        cutoff_time = datetime.now().timestamp() - (duration_minutes * 60)
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_usage": m.cpu_usage,
                "memory_usage": m.memory_usage,
                "active_tasks": m.active_tasks
            }
            for m in self.metrics_history
            if m.timestamp.timestamp() > cutoff_time
        ]
        
    async def export_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics
        """
        # TODO: Implement Prometheus export
        raise NotImplementedError("Prometheus export not yet implemented")