//! Cryptographic utilities for the protocol layer

use ed25519_dalek::{Keypair, PublicKey, Signature};
use ring::digest;

/// Generate a new keypair
pub fn generate_keypair() -> Keypair {
    let mut csprng = rand::rngs::OsRng;
    Keypair::generate(&mut csprng)
}

/// Hash data using SHA-256
pub fn hash_data(data: &[u8]) -> Vec<u8> {
    digest::digest(&digest::SHA256, data).as_ref().to_vec()
}

// TODO: Implement additional cryptographic functions