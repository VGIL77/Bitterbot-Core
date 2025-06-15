use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Represents a computational resource
#[derive(Debug, Clone)]
pub struct Resource {
    pub id: String,
    pub resource_type: ResourceType,
    pub capacity: u64,
    pub available: u64,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ResourceType {
    Cpu,
    Memory,
    Gpu,
    Storage,
}

/// ResourceManager handles allocation and tracking of computational resources
pub struct ResourceManager {
    resources: Arc<RwLock<HashMap<String, Resource>>>,
}

impl ResourceManager {
    /// Creates a new ResourceManager instance
    pub fn new() -> Self {
        Self {
            resources: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Registers a new resource
    pub fn register_resource(&self, resource: Resource) -> Result<(), String> {
        let mut resources = self.resources.write().unwrap();
        if resources.contains_key(&resource.id) {
            return Err("Resource already exists".to_string());
        }
        resources.insert(resource.id.clone(), resource);
        Ok(())
    }

    /// Allocates a specified amount of resource
    pub fn allocate(&self, resource_id: &str, amount: u64) -> Result<(), String> {
        let mut resources = self.resources.write().unwrap();
        match resources.get_mut(resource_id) {
            Some(resource) => {
                if resource.available < amount {
                    return Err("Insufficient resources available".to_string());
                }
                resource.available -= amount;
                Ok(())
            }
            None => Err("Resource not found".to_string()),
        }
    }

    /// Releases a specified amount of resource
    pub fn release(&self, resource_id: &str, amount: u64) -> Result<(), String> {
        let mut resources = self.resources.write().unwrap();
        match resources.get_mut(resource_id) {
            Some(resource) => {
                resource.available = (resource.available + amount).min(resource.capacity);
                Ok(())
            }
            None => Err("Resource not found".to_string()),
        }
    }

    /// Gets the current state of a resource
    pub fn get_resource_status(&self, resource_id: &str) -> Option<Resource> {
        let resources = self.resources.read().unwrap();
        resources.get(resource_id).cloned()
    }
}

impl Default for ResourceManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resource_manager_creation() {
        let manager = ResourceManager::new();
        assert!(manager.get_resource_status("test").is_none());
    }
}