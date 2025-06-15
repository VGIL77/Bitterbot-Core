use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

/// Status of a task execution
#[derive(Debug, Clone, PartialEq)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

/// Result of task execution
#[derive(Debug, Clone)]
pub struct ExecutionResult {
    pub task_id: String,
    pub status: TaskStatus,
    pub output: Option<Vec<u8>>,
    pub error: Option<String>,
    pub execution_time_ms: u64,
}

/// Configuration for task execution
#[derive(Debug, Clone)]
pub struct ExecutionConfig {
    pub max_execution_time_ms: u64,
    pub retry_attempts: u32,
    pub resource_limit: u64,
}

/// TaskExecutor handles the execution of computational tasks
pub struct TaskExecutor {
    config: ExecutionConfig,
    active_tasks: Arc<Mutex<Vec<String>>>,
    completed_count: Arc<Mutex<u64>>,
}

impl TaskExecutor {
    /// Creates a new TaskExecutor instance
    pub fn new(config: ExecutionConfig) -> Self {
        Self {
            config,
            active_tasks: Arc::new(Mutex::new(Vec::new())),
            completed_count: Arc::new(Mutex::new(0)),
        }
    }

    /// Executes a task with the given payload
    pub fn execute_task(&self, task_id: String, payload: Vec<u8>) -> ExecutionResult {
        // Add task to active list
        {
            let mut active = self.active_tasks.lock().unwrap();
            active.push(task_id.clone());
        }

        let start_time = std::time::Instant::now();
        
        // Simulate task execution (stub implementation)
        thread::sleep(Duration::from_millis(100));
        
        let execution_time_ms = start_time.elapsed().as_millis() as u64;
        
        // Remove from active list and increment completed count
        {
            let mut active = self.active_tasks.lock().unwrap();
            active.retain(|id| id != &task_id);
            
            let mut count = self.completed_count.lock().unwrap();
            *count += 1;
        }
        
        // Return stub result
        ExecutionResult {
            task_id,
            status: TaskStatus::Completed,
            output: Some(payload),
            error: None,
            execution_time_ms,
        }
    }

    /// Cancels a running task
    pub fn cancel_task(&self, task_id: &str) -> Result<(), String> {
        let mut active = self.active_tasks.lock().unwrap();
        if let Some(pos) = active.iter().position(|id| id == task_id) {
            active.remove(pos);
            Ok(())
        } else {
            Err("Task not found".to_string())
        }
    }

    /// Gets the list of currently active tasks
    pub fn get_active_tasks(&self) -> Vec<String> {
        let active = self.active_tasks.lock().unwrap();
        active.clone()
    }

    /// Gets the number of completed tasks
    pub fn get_completed_count(&self) -> u64 {
        *self.completed_count.lock().unwrap()
    }

    /// Checks if the executor can accept more tasks
    pub fn can_accept_task(&self) -> bool {
        let active = self.active_tasks.lock().unwrap();
        active.len() < 10 // Arbitrary limit for stub
    }
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            max_execution_time_ms: 60000,
            retry_attempts: 3,
            resource_limit: 1024 * 1024 * 1024, // 1GB
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_executor_creation() {
        let config = ExecutionConfig::default();
        let executor = TaskExecutor::new(config);
        assert_eq!(executor.get_completed_count(), 0);
        assert!(executor.can_accept_task());
    }
}