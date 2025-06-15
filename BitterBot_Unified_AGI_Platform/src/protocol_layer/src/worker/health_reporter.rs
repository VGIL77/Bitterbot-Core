use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

/// Health status of a component
#[derive(Debug, Clone, PartialEq)]
pub enum HealthStatus {
    Healthy,
    Degraded,
    Unhealthy,
    Unknown,
}

/// Health check result for a component
#[derive(Debug, Clone)]
pub struct HealthCheckResult {
    pub component_name: String,
    pub status: HealthStatus,
    pub message: Option<String>,
    pub last_check: Instant,
    pub response_time_ms: u64,
}

/// Overall system health report
#[derive(Debug, Clone)]
pub struct HealthReport {
    pub overall_status: HealthStatus,
    pub component_results: HashMap<String, HealthCheckResult>,
    pub timestamp: Instant,
    pub uptime_seconds: u64,
}

/// Component that can be health-checked
pub trait HealthCheckable {
    fn check_health(&self) -> HealthCheckResult;
    fn get_name(&self) -> String;
}

/// HealthReporter manages health checks for worker components
pub struct HealthReporter {
    components: Arc<RwLock<HashMap<String, Box<dyn HealthCheckable + Send + Sync>>>>,
    check_results: Arc<RwLock<HashMap<String, HealthCheckResult>>>,
    start_time: Instant,
    check_interval: Duration,
}

impl HealthReporter {
    /// Creates a new HealthReporter instance
    pub fn new(check_interval: Duration) -> Self {
        Self {
            components: Arc::new(RwLock::new(HashMap::new())),
            check_results: Arc::new(RwLock::new(HashMap::new())),
            start_time: Instant::now(),
            check_interval,
        }
    }

    /// Registers a component for health checking
    pub fn register_component(&self, name: String, component: Box<dyn HealthCheckable + Send + Sync>) {
        let mut components = self.components.write().unwrap();
        components.insert(name, component);
    }

    /// Performs health checks on all registered components
    pub fn run_health_checks(&self) {
        let components = self.components.read().unwrap();
        let mut results = self.check_results.write().unwrap();
        
        for (name, component) in components.iter() {
            let result = component.check_health();
            results.insert(name.clone(), result);
        }
    }

    /// Gets the current health report
    pub fn get_health_report(&self) -> HealthReport {
        let results = self.check_results.read().unwrap();
        let component_results = results.clone();
        
        // Determine overall status
        let overall_status = self.calculate_overall_status(&component_results);
        
        HealthReport {
            overall_status,
            component_results,
            timestamp: Instant::now(),
            uptime_seconds: self.start_time.elapsed().as_secs(),
        }
    }

    /// Calculates overall system health based on component statuses
    fn calculate_overall_status(&self, results: &HashMap<String, HealthCheckResult>) -> HealthStatus {
        if results.is_empty() {
            return HealthStatus::Unknown;
        }
        
        let unhealthy_count = results.values()
            .filter(|r| r.status == HealthStatus::Unhealthy)
            .count();
        
        let degraded_count = results.values()
            .filter(|r| r.status == HealthStatus::Degraded)
            .count();
        
        if unhealthy_count > 0 {
            HealthStatus::Unhealthy
        } else if degraded_count > 0 {
            HealthStatus::Degraded
        } else {
            HealthStatus::Healthy
        }
    }

    /// Gets the health status of a specific component
    pub fn get_component_health(&self, component_name: &str) -> Option<HealthCheckResult> {
        let results = self.check_results.read().unwrap();
        results.get(component_name).cloned()
    }

    /// Checks if the system is healthy
    pub fn is_healthy(&self) -> bool {
        let report = self.get_health_report();
        report.overall_status == HealthStatus::Healthy
    }

    /// Gets system uptime
    pub fn get_uptime(&self) -> Duration {
        self.start_time.elapsed()
    }
}

/// Example implementation of a health-checkable component
pub struct DummyComponent {
    name: String,
}

impl DummyComponent {
    pub fn new(name: String) -> Self {
        Self { name }
    }
}

impl HealthCheckable for DummyComponent {
    fn check_health(&self) -> HealthCheckResult {
        HealthCheckResult {
            component_name: self.name.clone(),
            status: HealthStatus::Healthy,
            message: Some("Component is functioning normally".to_string()),
            last_check: Instant::now(),
            response_time_ms: 10,
        }
    }

    fn get_name(&self) -> String {
        self.name.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_health_reporter_creation() {
        let reporter = HealthReporter::new(Duration::from_secs(30));
        assert!(reporter.is_healthy());
        assert!(reporter.get_uptime().as_secs() < 1);
    }
}