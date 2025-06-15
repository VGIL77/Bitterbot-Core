use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

/// System resource metrics
#[derive(Debug, Clone)]
pub struct ResourceMetrics {
    pub cpu_usage_percent: f64,
    pub memory_usage_bytes: u64,
    pub memory_total_bytes: u64,
    pub disk_usage_bytes: u64,
    pub disk_total_bytes: u64,
    pub network_rx_bytes: u64,
    pub network_tx_bytes: u64,
    pub timestamp: Instant,
}

/// Resource alerts
#[derive(Debug, Clone)]
pub struct ResourceAlert {
    pub alert_type: AlertType,
    pub metric_value: f64,
    pub threshold: f64,
    pub timestamp: Instant,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AlertType {
    HighCpuUsage,
    HighMemoryUsage,
    LowDiskSpace,
    NetworkCongestion,
}

/// Configuration for resource monitoring
#[derive(Debug, Clone)]
pub struct MonitorConfig {
    pub cpu_threshold: f64,
    pub memory_threshold: f64,
    pub disk_threshold: f64,
    pub sample_interval_ms: u64,
}

/// ResourceMonitor tracks system resource usage
pub struct ResourceMonitor {
    config: MonitorConfig,
    current_metrics: Arc<RwLock<ResourceMetrics>>,
    alerts: Arc<RwLock<Vec<ResourceAlert>>>,
    monitoring_active: Arc<RwLock<bool>>,
}

impl ResourceMonitor {
    /// Creates a new ResourceMonitor instance
    pub fn new(config: MonitorConfig) -> Self {
        let initial_metrics = ResourceMetrics {
            cpu_usage_percent: 0.0,
            memory_usage_bytes: 0,
            memory_total_bytes: 8 * 1024 * 1024 * 1024, // 8GB default
            disk_usage_bytes: 0,
            disk_total_bytes: 100 * 1024 * 1024 * 1024, // 100GB default
            network_rx_bytes: 0,
            network_tx_bytes: 0,
            timestamp: Instant::now(),
        };

        Self {
            config,
            current_metrics: Arc::new(RwLock::new(initial_metrics)),
            alerts: Arc::new(RwLock::new(Vec::new())),
            monitoring_active: Arc::new(RwLock::new(false)),
        }
    }

    /// Starts resource monitoring
    pub fn start_monitoring(&self) {
        let mut active = self.monitoring_active.write().unwrap();
        *active = true;
        
        // In a real implementation, this would spawn a monitoring thread
        self.update_metrics();
    }

    /// Stops resource monitoring
    pub fn stop_monitoring(&self) {
        let mut active = self.monitoring_active.write().unwrap();
        *active = false;
    }

    /// Updates resource metrics (stub implementation)
    fn update_metrics(&self) {
        let mut metrics = self.current_metrics.write().unwrap();
        
        // Simulate metric updates
        metrics.cpu_usage_percent = 25.0;
        metrics.memory_usage_bytes = 2 * 1024 * 1024 * 1024; // 2GB
        metrics.disk_usage_bytes = 30 * 1024 * 1024 * 1024; // 30GB
        metrics.network_rx_bytes += 1024;
        metrics.network_tx_bytes += 512;
        metrics.timestamp = Instant::now();
        
        // Check for alerts
        self.check_alerts(&metrics);
    }

    /// Checks current metrics against thresholds
    fn check_alerts(&self, metrics: &ResourceMetrics) {
        let mut alerts = self.alerts.write().unwrap();
        
        if metrics.cpu_usage_percent > self.config.cpu_threshold {
            alerts.push(ResourceAlert {
                alert_type: AlertType::HighCpuUsage,
                metric_value: metrics.cpu_usage_percent,
                threshold: self.config.cpu_threshold,
                timestamp: Instant::now(),
            });
        }
        
        let memory_usage_percent = (metrics.memory_usage_bytes as f64 / metrics.memory_total_bytes as f64) * 100.0;
        if memory_usage_percent > self.config.memory_threshold {
            alerts.push(ResourceAlert {
                alert_type: AlertType::HighMemoryUsage,
                metric_value: memory_usage_percent,
                threshold: self.config.memory_threshold,
                timestamp: Instant::now(),
            });
        }
    }

    /// Gets current resource metrics
    pub fn get_current_metrics(&self) -> ResourceMetrics {
        self.current_metrics.read().unwrap().clone()
    }

    /// Gets recent alerts
    pub fn get_alerts(&self) -> Vec<ResourceAlert> {
        self.alerts.read().unwrap().clone()
    }

    /// Clears alert history
    pub fn clear_alerts(&self) {
        let mut alerts = self.alerts.write().unwrap();
        alerts.clear();
    }

    /// Checks if monitoring is active
    pub fn is_monitoring(&self) -> bool {
        *self.monitoring_active.read().unwrap()
    }
}

impl Default for MonitorConfig {
    fn default() -> Self {
        Self {
            cpu_threshold: 80.0,
            memory_threshold: 90.0,
            disk_threshold: 95.0,
            sample_interval_ms: 1000,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resource_monitor_creation() {
        let config = MonitorConfig::default();
        let monitor = ResourceMonitor::new(config);
        assert!(!monitor.is_monitoring());
        assert!(monitor.get_alerts().is_empty());
    }
}