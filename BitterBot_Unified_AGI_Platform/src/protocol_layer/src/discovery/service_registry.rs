use std::collections::{HashMap, HashSet};
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

/// Service metadata
#[derive(Debug, Clone)]
pub struct ServiceInfo {
    pub service_id: String,
    pub service_type: ServiceType,
    pub version: String,
    pub endpoint: String,
    pub capabilities: Vec<String>,
    pub health_check_endpoint: Option<String>,
    pub metadata: HashMap<String, String>,
    pub registered_at: Instant,
    pub last_heartbeat: Instant,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum ServiceType {
    Orchestrator,
    Validator,
    Worker,
    Storage,
    Monitoring,
    Gateway,
    Custom(String),
}

/// Service query parameters
#[derive(Debug, Clone, Default)]
pub struct ServiceQuery {
    pub service_type: Option<ServiceType>,
    pub capabilities: Vec<String>,
    pub version: Option<String>,
    pub metadata_filters: HashMap<String, String>,
}

/// Service registration request
#[derive(Debug, Clone)]
pub struct ServiceRegistration {
    pub service_id: String,
    pub service_type: ServiceType,
    pub version: String,
    pub endpoint: String,
    pub capabilities: Vec<String>,
    pub health_check_endpoint: Option<String>,
    pub metadata: HashMap<String, String>,
    pub ttl: Duration,
}

/// ServiceRegistry manages service discovery and registration
pub struct ServiceRegistry {
    services: Arc<RwLock<HashMap<String, ServiceInfo>>>,
    service_index: Arc<RwLock<HashMap<ServiceType, HashSet<String>>>>,
    capability_index: Arc<RwLock<HashMap<String, HashSet<String>>>>,
    heartbeat_timeout: Duration,
}

impl ServiceRegistry {
    /// Creates a new ServiceRegistry instance
    pub fn new(heartbeat_timeout: Duration) -> Self {
        Self {
            services: Arc::new(RwLock::new(HashMap::new())),
            service_index: Arc::new(RwLock::new(HashMap::new())),
            capability_index: Arc::new(RwLock::new(HashMap::new())),
            heartbeat_timeout,
        }
    }

    /// Registers a new service
    pub fn register_service(&self, registration: ServiceRegistration) -> Result<(), String> {
        let mut services = self.services.write().unwrap();
        
        if services.contains_key(&registration.service_id) {
            return Err("Service already registered".to_string());
        }
        
        let service_info = ServiceInfo {
            service_id: registration.service_id.clone(),
            service_type: registration.service_type.clone(),
            version: registration.version,
            endpoint: registration.endpoint,
            capabilities: registration.capabilities.clone(),
            health_check_endpoint: registration.health_check_endpoint,
            metadata: registration.metadata,
            registered_at: Instant::now(),
            last_heartbeat: Instant::now(),
        };
        
        // Update indices
        let mut service_index = self.service_index.write().unwrap();
        service_index
            .entry(registration.service_type.clone())
            .or_insert_with(HashSet::new)
            .insert(registration.service_id.clone());
        
        let mut capability_index = self.capability_index.write().unwrap();
        for capability in &registration.capabilities {
            capability_index
                .entry(capability.clone())
                .or_insert_with(HashSet::new)
                .insert(registration.service_id.clone());
        }
        
        services.insert(registration.service_id, service_info);
        Ok(())
    }

    /// Deregisters a service
    pub fn deregister_service(&self, service_id: &str) -> Result<(), String> {
        let mut services = self.services.write().unwrap();
        
        match services.remove(service_id) {
            Some(service_info) => {
                // Update indices
                let mut service_index = self.service_index.write().unwrap();
                if let Some(service_set) = service_index.get_mut(&service_info.service_type) {
                    service_set.remove(service_id);
                }
                
                let mut capability_index = self.capability_index.write().unwrap();
                for capability in &service_info.capabilities {
                    if let Some(capability_set) = capability_index.get_mut(capability) {
                        capability_set.remove(service_id);
                    }
                }
                
                Ok(())
            }
            None => Err("Service not found".to_string()),
        }
    }

    /// Updates service heartbeat
    pub fn heartbeat(&self, service_id: &str) -> Result<(), String> {
        let mut services = self.services.write().unwrap();
        
        match services.get_mut(service_id) {
            Some(service) => {
                service.last_heartbeat = Instant::now();
                Ok(())
            }
            None => Err("Service not found".to_string()),
        }
    }

    /// Queries services based on criteria
    pub fn query_services(&self, query: ServiceQuery) -> Vec<ServiceInfo> {
        let services = self.services.read().unwrap();
        
        services
            .values()
            .filter(|service| {
                // Filter by service type
                if let Some(ref service_type) = query.service_type {
                    if &service.service_type != service_type {
                        return false;
                    }
                }
                
                // Filter by capabilities
                if !query.capabilities.is_empty() {
                    if !query.capabilities.iter().all(|cap| service.capabilities.contains(cap)) {
                        return false;
                    }
                }
                
                // Filter by version
                if let Some(ref version) = query.version {
                    if &service.version != version {
                        return false;
                    }
                }
                
                // Filter by metadata
                for (key, value) in &query.metadata_filters {
                    match service.metadata.get(key) {
                        Some(v) if v == value => continue,
                        _ => return false,
                    }
                }
                
                true
            })
            .cloned()
            .collect()
    }

    /// Gets a specific service by ID
    pub fn get_service(&self, service_id: &str) -> Option<ServiceInfo> {
        let services = self.services.read().unwrap();
        services.get(service_id).cloned()
    }

    /// Gets all services of a specific type
    pub fn get_services_by_type(&self, service_type: &ServiceType) -> Vec<ServiceInfo> {
        let service_index = self.service_index.read().unwrap();
        let services = self.services.read().unwrap();
        
        if let Some(service_ids) = service_index.get(service_type) {
            service_ids
                .iter()
                .filter_map(|id| services.get(id).cloned())
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Removes stale services that haven't sent heartbeats
    pub fn cleanup_stale_services(&self) {
        let now = Instant::now();
        let mut services = self.services.write().unwrap();
        let mut to_remove = Vec::new();
        
        for (id, service) in services.iter() {
            if now.duration_since(service.last_heartbeat) > self.heartbeat_timeout {
                to_remove.push(id.clone());
            }
        }
        
        drop(services);
        
        for service_id in to_remove {
            let _ = self.deregister_service(&service_id);
        }
    }

    /// Gets the total number of registered services
    pub fn service_count(&self) -> usize {
        let services = self.services.read().unwrap();
        services.len()
    }

    /// Gets all registered service types
    pub fn get_service_types(&self) -> Vec<ServiceType> {
        let service_index = self.service_index.read().unwrap();
        service_index.keys().cloned().collect()
    }
}

impl Default for ServiceRegistry {
    fn default() -> Self {
        Self::new(Duration::from_secs(300))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_service_registry_creation() {
        let registry = ServiceRegistry::default();
        assert_eq!(registry.service_count(), 0);
    }
}