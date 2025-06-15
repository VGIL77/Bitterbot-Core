use std::collections::VecDeque;
use std::sync::{Arc, Mutex};

/// Represents a task to be scheduled
#[derive(Debug, Clone)]
pub struct Task {
    pub id: String,
    pub priority: u8,
    pub payload: Vec<u8>,
}

/// TaskScheduler manages task distribution and scheduling
pub struct TaskScheduler {
    task_queue: Arc<Mutex<VecDeque<Task>>>,
    max_queue_size: usize,
}

impl TaskScheduler {
    /// Creates a new TaskScheduler instance
    pub fn new(max_queue_size: usize) -> Self {
        Self {
            task_queue: Arc::new(Mutex::new(VecDeque::new())),
            max_queue_size,
        }
    }

    /// Schedules a task for execution
    pub fn schedule_task(&self, task: Task) -> Result<(), String> {
        let mut queue = self.task_queue.lock().unwrap();
        if queue.len() >= self.max_queue_size {
            return Err("Task queue is full".to_string());
        }
        queue.push_back(task);
        Ok(())
    }

    /// Retrieves the next task to execute
    pub fn get_next_task(&self) -> Option<Task> {
        let mut queue = self.task_queue.lock().unwrap();
        queue.pop_front()
    }

    /// Returns the current number of pending tasks
    pub fn pending_task_count(&self) -> usize {
        let queue = self.task_queue.lock().unwrap();
        queue.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_scheduler_creation() {
        let scheduler = TaskScheduler::new(100);
        assert_eq!(scheduler.pending_task_count(), 0);
    }
}