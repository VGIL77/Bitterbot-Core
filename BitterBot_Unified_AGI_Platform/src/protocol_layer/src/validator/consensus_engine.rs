use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Represents a vote in the consensus process
#[derive(Debug, Clone)]
pub struct Vote {
    pub validator_id: String,
    pub block_hash: String,
    pub timestamp: u64,
    pub signature: Vec<u8>,
}

/// Represents the current consensus state
#[derive(Debug, Clone, PartialEq)]
pub enum ConsensusState {
    Idle,
    Proposing,
    Voting,
    Finalizing,
    Committed,
}

/// ConsensusEngine manages the consensus protocol for validation
pub struct ConsensusEngine {
    state: Arc<RwLock<ConsensusState>>,
    votes: Arc<RwLock<HashMap<String, Vec<Vote>>>>,
    threshold: f64,
    validator_count: usize,
}

impl ConsensusEngine {
    /// Creates a new ConsensusEngine instance
    pub fn new(threshold: f64, validator_count: usize) -> Self {
        Self {
            state: Arc::new(RwLock::new(ConsensusState::Idle)),
            votes: Arc::new(RwLock::new(HashMap::new())),
            threshold,
            validator_count,
        }
    }

    /// Submits a vote for a block
    pub fn submit_vote(&self, vote: Vote) -> Result<(), String> {
        let mut votes = self.votes.write().unwrap();
        let block_votes = votes.entry(vote.block_hash.clone()).or_insert_with(Vec::new);
        
        // Check if validator already voted
        if block_votes.iter().any(|v| v.validator_id == vote.validator_id) {
            return Err("Validator already voted for this block".to_string());
        }
        
        block_votes.push(vote);
        Ok(())
    }

    /// Checks if consensus has been reached for a block
    pub fn check_consensus(&self, block_hash: &str) -> bool {
        let votes = self.votes.read().unwrap();
        if let Some(block_votes) = votes.get(block_hash) {
            let vote_count = block_votes.len() as f64;
            let required_votes = (self.validator_count as f64 * self.threshold).ceil();
            vote_count >= required_votes
        } else {
            false
        }
    }

    /// Gets the current consensus state
    pub fn get_state(&self) -> ConsensusState {
        self.state.read().unwrap().clone()
    }

    /// Updates the consensus state
    pub fn set_state(&self, new_state: ConsensusState) {
        let mut state = self.state.write().unwrap();
        *state = new_state;
    }

    /// Resets the consensus engine for a new round
    pub fn reset(&self) {
        let mut votes = self.votes.write().unwrap();
        votes.clear();
        self.set_state(ConsensusState::Idle);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_consensus_engine_creation() {
        let engine = ConsensusEngine::new(0.67, 10);
        assert_eq!(engine.get_state(), ConsensusState::Idle);
    }
}