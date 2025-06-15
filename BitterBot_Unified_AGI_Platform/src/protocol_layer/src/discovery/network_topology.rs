use std::collections::{HashMap, HashSet};
use std::sync::{Arc, RwLock};

/// Represents a node in the network topology
#[derive(Debug, Clone)]
pub struct NetworkNode {
    pub node_id: String,
    pub node_type: NodeType,
    pub region: String,
    pub capacity: NodeCapacity,
    pub connections: HashSet<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum NodeType {
    Orchestrator,
    Validator,
    Worker,
    Gateway,
}

/// Node capacity information
#[derive(Debug, Clone)]
pub struct NodeCapacity {
    pub cpu_cores: u32,
    pub memory_gb: u32,
    pub bandwidth_mbps: u32,
    pub storage_gb: u32,
}

/// Edge between two nodes
#[derive(Debug, Clone)]
pub struct NetworkEdge {
    pub from_node: String,
    pub to_node: String,
    pub latency_ms: u64,
    pub bandwidth_mbps: u32,
    pub reliability: f64,
}

/// Network statistics
#[derive(Debug, Clone)]
pub struct NetworkStats {
    pub total_nodes: usize,
    pub nodes_by_type: HashMap<NodeType, usize>,
    pub average_connections: f64,
    pub network_diameter: u32,
    pub clustering_coefficient: f64,
}

/// NetworkTopology manages the network graph structure
pub struct NetworkTopology {
    nodes: Arc<RwLock<HashMap<String, NetworkNode>>>,
    edges: Arc<RwLock<Vec<NetworkEdge>>>,
    regions: Arc<RwLock<HashSet<String>>>,
}

impl NetworkTopology {
    /// Creates a new NetworkTopology instance
    pub fn new() -> Self {
        Self {
            nodes: Arc::new(RwLock::new(HashMap::new())),
            edges: Arc::new(RwLock::new(Vec::new())),
            regions: Arc::new(RwLock::new(HashSet::new())),
        }
    }

    /// Adds a node to the topology
    pub fn add_node(&self, node: NetworkNode) -> Result<(), String> {
        let mut nodes = self.nodes.write().unwrap();
        if nodes.contains_key(&node.node_id) {
            return Err("Node already exists".to_string());
        }
        
        let mut regions = self.regions.write().unwrap();
        regions.insert(node.region.clone());
        
        nodes.insert(node.node_id.clone(), node);
        Ok(())
    }

    /// Removes a node from the topology
    pub fn remove_node(&self, node_id: &str) -> Result<(), String> {
        let mut nodes = self.nodes.write().unwrap();
        if nodes.remove(node_id).is_none() {
            return Err("Node not found".to_string());
        }
        
        // Remove all edges connected to this node
        let mut edges = self.edges.write().unwrap();
        edges.retain(|edge| edge.from_node != node_id && edge.to_node != node_id);
        
        Ok(())
    }

    /// Adds an edge between two nodes
    pub fn add_edge(&self, edge: NetworkEdge) -> Result<(), String> {
        let nodes = self.nodes.read().unwrap();
        
        // Verify both nodes exist
        if !nodes.contains_key(&edge.from_node) || !nodes.contains_key(&edge.to_node) {
            return Err("One or both nodes not found".to_string());
        }
        
        // Update node connections
        drop(nodes);
        let mut nodes = self.nodes.write().unwrap();
        
        if let Some(from_node) = nodes.get_mut(&edge.from_node) {
            from_node.connections.insert(edge.to_node.clone());
        }
        
        if let Some(to_node) = nodes.get_mut(&edge.to_node) {
            to_node.connections.insert(edge.from_node.clone());
        }
        
        drop(nodes);
        
        let mut edges = self.edges.write().unwrap();
        edges.push(edge);
        
        Ok(())
    }

    /// Gets a node by ID
    pub fn get_node(&self, node_id: &str) -> Option<NetworkNode> {
        let nodes = self.nodes.read().unwrap();
        nodes.get(node_id).cloned()
    }

    /// Gets all nodes of a specific type
    pub fn get_nodes_by_type(&self, node_type: NodeType) -> Vec<NetworkNode> {
        let nodes = self.nodes.read().unwrap();
        nodes
            .values()
            .filter(|n| n.node_type == node_type)
            .cloned()
            .collect()
    }

    /// Gets all nodes in a specific region
    pub fn get_nodes_by_region(&self, region: &str) -> Vec<NetworkNode> {
        let nodes = self.nodes.read().unwrap();
        nodes
            .values()
            .filter(|n| n.region == region)
            .cloned()
            .collect()
    }

    /// Finds the shortest path between two nodes (stub implementation)
    pub fn find_shortest_path(&self, from: &str, to: &str) -> Option<Vec<String>> {
        let nodes = self.nodes.read().unwrap();
        
        if !nodes.contains_key(from) || !nodes.contains_key(to) {
            return None;
        }
        
        // Stub: return direct path
        Some(vec![from.to_string(), to.to_string()])
    }

    /// Gets network statistics
    pub fn get_network_stats(&self) -> NetworkStats {
        let nodes = self.nodes.read().unwrap();
        let edges = self.edges.read().unwrap();
        
        let mut nodes_by_type = HashMap::new();
        let mut total_connections = 0;
        
        for node in nodes.values() {
            *nodes_by_type.entry(node.node_type.clone()).or_insert(0) += 1;
            total_connections += node.connections.len();
        }
        
        let average_connections = if !nodes.is_empty() {
            total_connections as f64 / nodes.len() as f64
        } else {
            0.0
        };
        
        NetworkStats {
            total_nodes: nodes.len(),
            nodes_by_type,
            average_connections,
            network_diameter: 3, // Stub value
            clustering_coefficient: 0.6, // Stub value
        }
    }

    /// Gets all regions in the network
    pub fn get_regions(&self) -> Vec<String> {
        let regions = self.regions.read().unwrap();
        regions.iter().cloned().collect()
    }

    /// Checks if the network is connected
    pub fn is_connected(&self) -> bool {
        let nodes = self.nodes.read().unwrap();
        if nodes.is_empty() {
            return true;
        }
        
        // Stub: assume connected if all nodes have at least one connection
        nodes.values().all(|node| !node.connections.is_empty())
    }
}

impl Default for NetworkTopology {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_network_topology_creation() {
        let topology = NetworkTopology::new();
        let stats = topology.get_network_stats();
        assert_eq!(stats.total_nodes, 0);
    }
}