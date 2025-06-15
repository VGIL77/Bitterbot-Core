use std::collections::{HashMap, HashSet};
use std::net::SocketAddr;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

/// Information about a discovered peer
#[derive(Debug, Clone)]
pub struct PeerInfo {
    pub peer_id: String,
    pub address: SocketAddr,
    pub capabilities: Vec<String>,
    pub last_seen: Instant,
    pub latency_ms: Option<u64>,
    pub version: String,
}

/// Peer discovery protocol types
#[derive(Debug, Clone, PartialEq)]
pub enum DiscoveryProtocol {
    Multicast,
    DHT,
    Bootstrap,
    Manual,
}

/// Configuration for peer discovery
#[derive(Debug, Clone)]
pub struct DiscoveryConfig {
    pub protocols: Vec<DiscoveryProtocol>,
    pub max_peers: usize,
    pub discovery_interval: Duration,
    pub peer_timeout: Duration,
    pub bootstrap_nodes: Vec<SocketAddr>,
}

/// PeerDiscovery manages finding and maintaining connections to network peers
pub struct PeerDiscovery {
    config: DiscoveryConfig,
    known_peers: Arc<RwLock<HashMap<String, PeerInfo>>>,
    active_discoveries: Arc<RwLock<HashSet<DiscoveryProtocol>>>,
    discovery_enabled: Arc<RwLock<bool>>,
}

impl PeerDiscovery {
    /// Creates a new PeerDiscovery instance
    pub fn new(config: DiscoveryConfig) -> Self {
        Self {
            config,
            known_peers: Arc::new(RwLock::new(HashMap::new())),
            active_discoveries: Arc::new(RwLock::new(HashSet::new())),
            discovery_enabled: Arc::new(RwLock::new(false)),
        }
    }

    /// Starts peer discovery process
    pub fn start_discovery(&self) -> Result<(), String> {
        let mut enabled = self.discovery_enabled.write().unwrap();
        if *enabled {
            return Err("Discovery already running".to_string());
        }
        *enabled = true;

        // Initialize discovery protocols
        for protocol in &self.config.protocols {
            self.start_protocol(protocol.clone())?;
        }

        Ok(())
    }

    /// Stops peer discovery
    pub fn stop_discovery(&self) {
        let mut enabled = self.discovery_enabled.write().unwrap();
        *enabled = false;
        
        let mut active = self.active_discoveries.write().unwrap();
        active.clear();
    }

    /// Starts a specific discovery protocol
    fn start_protocol(&self, protocol: DiscoveryProtocol) -> Result<(), String> {
        let mut active = self.active_discoveries.write().unwrap();
        if active.contains(&protocol) {
            return Err(format!("Protocol {:?} already active", protocol));
        }
        
        active.insert(protocol.clone());
        
        // Stub implementation - in reality would start protocol-specific discovery
        match protocol {
            DiscoveryProtocol::Bootstrap => self.discover_from_bootstrap(),
            _ => Ok(()),
        }
    }

    /// Discovers peers from bootstrap nodes
    fn discover_from_bootstrap(&self) -> Result<(), String> {
        for (i, addr) in self.config.bootstrap_nodes.iter().enumerate() {
            let peer_info = PeerInfo {
                peer_id: format!("bootstrap-{}", i),
                address: *addr,
                capabilities: vec!["validator".to_string(), "worker".to_string()],
                last_seen: Instant::now(),
                latency_ms: Some(10),
                version: "1.0.0".to_string(),
            };
            self.add_peer(peer_info)?;
        }
        Ok(())
    }

    /// Adds a discovered peer
    pub fn add_peer(&self, peer: PeerInfo) -> Result<(), String> {
        let mut peers = self.known_peers.write().unwrap();
        
        if peers.len() >= self.config.max_peers {
            return Err("Maximum peer limit reached".to_string());
        }
        
        peers.insert(peer.peer_id.clone(), peer);
        Ok(())
    }

    /// Removes a peer
    pub fn remove_peer(&self, peer_id: &str) -> Result<(), String> {
        let mut peers = self.known_peers.write().unwrap();
        if peers.remove(peer_id).is_none() {
            return Err("Peer not found".to_string());
        }
        Ok(())
    }

    /// Updates peer information
    pub fn update_peer(&self, peer_id: &str, latency_ms: u64) -> Result<(), String> {
        let mut peers = self.known_peers.write().unwrap();
        match peers.get_mut(peer_id) {
            Some(peer) => {
                peer.last_seen = Instant::now();
                peer.latency_ms = Some(latency_ms);
                Ok(())
            }
            None => Err("Peer not found".to_string()),
        }
    }

    /// Gets all known peers
    pub fn get_peers(&self) -> Vec<PeerInfo> {
        let peers = self.known_peers.read().unwrap();
        peers.values().cloned().collect()
    }

    /// Gets peers with specific capability
    pub fn get_peers_by_capability(&self, capability: &str) -> Vec<PeerInfo> {
        let peers = self.known_peers.read().unwrap();
        peers
            .values()
            .filter(|p| p.capabilities.contains(&capability.to_string()))
            .cloned()
            .collect()
    }

    /// Removes stale peers
    pub fn cleanup_stale_peers(&self) {
        let mut peers = self.known_peers.write().unwrap();
        let now = Instant::now();
        
        peers.retain(|_, peer| {
            now.duration_since(peer.last_seen) < self.config.peer_timeout
        });
    }

    /// Gets the number of active peers
    pub fn peer_count(&self) -> usize {
        let peers = self.known_peers.read().unwrap();
        peers.len()
    }

    /// Checks if discovery is enabled
    pub fn is_discovering(&self) -> bool {
        *self.discovery_enabled.read().unwrap()
    }
}

impl Default for DiscoveryConfig {
    fn default() -> Self {
        Self {
            protocols: vec![DiscoveryProtocol::Bootstrap, DiscoveryProtocol::DHT],
            max_peers: 100,
            discovery_interval: Duration::from_secs(30),
            peer_timeout: Duration::from_secs(300),
            bootstrap_nodes: vec![],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peer_discovery_creation() {
        let config = DiscoveryConfig::default();
        let discovery = PeerDiscovery::new(config);
        assert_eq!(discovery.peer_count(), 0);
        assert!(!discovery.is_discovering());
    }
}