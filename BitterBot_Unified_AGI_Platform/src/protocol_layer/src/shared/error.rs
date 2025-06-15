//! Error types for the protocol layer

use thiserror::Error;

/// Protocol layer error types
#[derive(Error, Debug)]
pub enum ProtocolError {
    /// Task-related errors
    #[error("Task error: {0}")]
    Task(String),
    
    /// Worker-related errors
    #[error("Worker error: {0}")]
    Worker(String),
    
    /// Consensus errors
    #[error("Consensus error: {0}")]
    Consensus(String),
    
    /// Network errors
    #[error("Network error: {0}")]
    Network(String),
    
    /// Database errors
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    /// Serialization errors
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    /// Configuration errors
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    /// Authentication errors
    #[error("Authentication error: {0}")]
    Authentication(String),
    
    /// Resource exhaustion
    #[error("Resource exhausted: {0}")]
    ResourceExhausted(String),
    
    /// Internal errors
    #[error("Internal error: {0}")]
    Internal(String),
    
    /// Other errors
    #[error(transparent)]
    Other(#[from] anyhow::Error),
}

/// Result type alias for protocol operations
pub type Result<T> = std::result::Result<T, ProtocolError>;