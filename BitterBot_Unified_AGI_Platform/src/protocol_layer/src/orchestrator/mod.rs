//! Task orchestration module

pub mod task_scheduler;
pub mod resource_manager;
pub mod coordination_engine;

pub use coordination_engine::CoordinationEngine;