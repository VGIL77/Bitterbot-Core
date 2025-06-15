//! Shared utilities and types for the protocol layer

pub mod types;
pub mod error;
pub mod crypto;
pub mod utils;

// Re-export commonly used items
pub use types::*;
pub use error::{ProtocolError, Result};