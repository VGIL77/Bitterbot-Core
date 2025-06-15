//! BitterBot Protocol Layer
//! 
//! This crate provides the decentralized protocol infrastructure for the
//! BitterBot AGI Platform, including task orchestration, validation,
//! worker management, and service discovery.

#![warn(missing_docs)]
#![warn(clippy::all)]

pub mod orchestrator;
pub mod validator;
pub mod worker;
pub mod discovery;
pub mod shared;

// Re-export commonly used types
pub use shared::{
    types::{Task, TaskResult, TaskStatus, NodeId, WorkerId},
    error::{ProtocolError, Result},
};

/// Protocol version for compatibility checking
pub const PROTOCOL_VERSION: &str = "0.1.0";

/// Initialize the protocol layer with default configuration
pub async fn initialize() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();
    
    tracing::info!("Initializing BitterBot Protocol Layer v{}", PROTOCOL_VERSION);
    
    Ok(())
}