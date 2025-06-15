use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Represents a validator's reputation score
#[derive(Debug, Clone)]
pub struct ReputationScore {
    pub validator_id: String,
    pub score: f64,
    pub successful_validations: u64,
    pub failed_validations: u64,
    pub last_updated: u64,
}

/// Events that affect reputation
#[derive(Debug, Clone)]
pub enum ReputationEvent {
    SuccessfulValidation,
    FailedValidation,
    MissedValidation,
    MaliciousBehavior,
}

/// ReputationSystem manages validator reputation scores
pub struct ReputationSystem {
    scores: Arc<RwLock<HashMap<String, ReputationScore>>>,
    base_score: f64,
    max_score: f64,
    min_score: f64,
}

impl ReputationSystem {
    /// Creates a new ReputationSystem instance
    pub fn new(base_score: f64, min_score: f64, max_score: f64) -> Self {
        Self {
            scores: Arc::new(RwLock::new(HashMap::new())),
            base_score,
            max_score,
            min_score,
        }
    }

    /// Registers a new validator with base reputation
    pub fn register_validator(&self, validator_id: String) -> Result<(), String> {
        let mut scores = self.scores.write().unwrap();
        if scores.contains_key(&validator_id) {
            return Err("Validator already registered".to_string());
        }
        
        let score = ReputationScore {
            validator_id: validator_id.clone(),
            score: self.base_score,
            successful_validations: 0,
            failed_validations: 0,
            last_updated: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };
        
        scores.insert(validator_id, score);
        Ok(())
    }

    /// Updates a validator's reputation based on an event
    pub fn update_reputation(&self, validator_id: &str, event: ReputationEvent) -> Result<(), String> {
        let mut scores = self.scores.write().unwrap();
        match scores.get_mut(validator_id) {
            Some(score) => {
                match event {
                    ReputationEvent::SuccessfulValidation => {
                        score.successful_validations += 1;
                        score.score = (score.score + 1.0).min(self.max_score);
                    }
                    ReputationEvent::FailedValidation => {
                        score.failed_validations += 1;
                        score.score = (score.score - 2.0).max(self.min_score);
                    }
                    ReputationEvent::MissedValidation => {
                        score.score = (score.score - 1.0).max(self.min_score);
                    }
                    ReputationEvent::MaliciousBehavior => {
                        score.score = (score.score - 10.0).max(self.min_score);
                    }
                }
                score.last_updated = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs();
                Ok(())
            }
            None => Err("Validator not found".to_string()),
        }
    }

    /// Gets a validator's reputation score
    pub fn get_reputation(&self, validator_id: &str) -> Option<ReputationScore> {
        let scores = self.scores.read().unwrap();
        scores.get(validator_id).cloned()
    }

    /// Gets validators with reputation above a threshold
    pub fn get_validators_above_threshold(&self, threshold: f64) -> Vec<String> {
        let scores = self.scores.read().unwrap();
        scores
            .values()
            .filter(|score| score.score >= threshold)
            .map(|score| score.validator_id.clone())
            .collect()
    }

    /// Checks if a validator is eligible based on reputation
    pub fn is_validator_eligible(&self, validator_id: &str, min_required_score: f64) -> bool {
        if let Some(score) = self.get_reputation(validator_id) {
            score.score >= min_required_score
        } else {
            false
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reputation_system_creation() {
        let system = ReputationSystem::new(50.0, 0.0, 100.0);
        assert!(system.get_reputation("test").is_none());
    }
}