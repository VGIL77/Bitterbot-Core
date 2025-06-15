//! Utility functions for the protocol layer

use std::time::{SystemTime, UNIX_EPOCH};

/// Get current timestamp in milliseconds
pub fn timestamp_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_millis() as u64
}

/// Generate a random ID
pub fn generate_id() -> uuid::Uuid {
    uuid::Uuid::new_v4()
}

// TODO: Add more utility functions