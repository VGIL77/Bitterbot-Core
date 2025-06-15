//! Shared types for the protocol layer

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

/// Node identifier
pub type NodeId = Uuid;

/// Worker identifier
pub type WorkerId = Uuid;

/// Task identifier
pub type TaskId = Uuid;

/// Task status enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskStatus {
    /// Task is pending assignment
    Pending,
    /// Task has been assigned to a worker
    Assigned,
    /// Task is currently being executed
    Running,
    /// Task completed successfully
    Completed,
    /// Task failed during execution
    Failed,
    /// Task was cancelled
    Cancelled,
}

/// Task priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Priority {
    /// Lowest priority
    Low = 1,
    /// Normal priority
    Normal = 5,
    /// High priority
    High = 8,
    /// Critical priority
    Critical = 10,
}

/// Represents a distributed task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    /// Unique task identifier
    pub id: TaskId,
    /// Task type/category
    pub task_type: String,
    /// Task payload data
    pub payload: serde_json::Value,
    /// Task priority
    pub priority: Priority,
    /// Task status
    pub status: TaskStatus,
    /// Worker assigned to this task
    pub assigned_worker: Option<WorkerId>,
    /// Task creation timestamp
    pub created_at: DateTime<Utc>,
    /// Task update timestamp
    pub updated_at: DateTime<Utc>,
    /// Task metadata
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Result of task execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult {
    /// Task identifier
    pub task_id: TaskId,
    /// Execution success status
    pub success: bool,
    /// Result data
    pub data: Option<serde_json::Value>,
    /// Error message if failed
    pub error: Option<String>,
    /// Execution duration in milliseconds
    pub duration_ms: u64,
    /// Resource usage metrics
    pub metrics: TaskMetrics,
}

/// Task execution metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskMetrics {
    /// CPU usage percentage
    pub cpu_usage: f32,
    /// Memory usage in bytes
    pub memory_bytes: u64,
    /// Network bytes sent
    pub network_sent: u64,
    /// Network bytes received
    pub network_received: u64,
}

/// Worker node information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerInfo {
    /// Worker identifier
    pub id: WorkerId,
    /// Worker capabilities
    pub capabilities: Vec<String>,
    /// Available resources
    pub resources: WorkerResources,
    /// Current load (0.0 - 1.0)
    pub load: f32,
    /// Health status
    pub healthy: bool,
    /// Last heartbeat timestamp
    pub last_heartbeat: DateTime<Utc>,
}

/// Worker resource availability
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkerResources {
    /// Available CPU cores
    pub cpu_cores: u32,
    /// Available memory in bytes
    pub memory_bytes: u64,
    /// Available GPU devices
    pub gpu_count: u32,
    /// Available disk space in bytes
    pub disk_bytes: u64,
}

/// Service discovery entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceEntry {
    /// Service name
    pub name: String,
    /// Service type
    pub service_type: String,
    /// Service endpoint
    pub endpoint: String,
    /// Service metadata
    pub metadata: HashMap<String, String>,
    /// Registration timestamp
    pub registered_at: DateTime<Utc>,
}

/// Consensus proposal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Proposal {
    /// Proposal identifier
    pub id: Uuid,
    /// Proposal type
    pub proposal_type: ProposalType,
    /// Proposal data
    pub data: serde_json::Value,
    /// Proposer node
    pub proposer: NodeId,
    /// Creation timestamp
    pub created_at: DateTime<Utc>,
}

/// Types of consensus proposals
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ProposalType {
    /// Task assignment proposal
    TaskAssignment,
    /// Worker registration
    WorkerRegistration,
    /// Configuration change
    ConfigurationChange,
    /// Protocol upgrade
    ProtocolUpgrade,
}

impl Default for Priority {
    fn default() -> Self {
        Priority::Normal
    }
}