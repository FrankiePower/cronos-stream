// config.rs - Load configuration from environment variables

use alloy::primitives::Address;
use std::{env::var, num::ParseIntError};

/// Configuration loaded from environment variables

#[derive(Debug, Clone)]
pub struct Config {
    /// Port the HTTP server listens on (e.g., 3000)
    pub port: u16,

    /// PostgreSQL connection string
    /// e.g., "postgres://user:pass@localhost:5432/cronos_stream"
    pub database_url: String,

    /// Blockchain RPC endpoint
    /// e.g., "https://evm-t3.cronos.org"
    pub rpc_url: String,

    /// Chain ID for EIP-712 signatures
    /// Cronos testnet = 338, Cronos mainnet = 25
    pub chain_id: u64,

    /// Sequencer's private key (hex string with 0x prefix)
    /// This wallet co-signs all vouchers
    pub sequencer_private_key: String,

    /// Address of the StreamChannel smart contract
    pub channel_manager: Address,
}

impl Config {
    /// Load configuration from environment variables
    ///
    /// Returns `Result<Config, String>`:
    /// - `Ok(Config)` if all required vars are present
    /// - `Err(String)` with error message if something is missing
    ///
    /// The `?` operator propagates errors - if `get_env` returns Err,
    /// this function immediately returns that Err.

    pub fn from_env() -> Result<Self, String> {
        Ok(Config {
            // Parse port as u16 (unsigned 16-bit integer, 0-65535)
            // `get_env` returns String, `.parse()` converts to u16
            // `.map_err(|e| e.to_string())?` converts parse errors to String
            port: get_env("PORT")?
                .parse()
                .map_err(|e: ParseIntError| e.to_string())?,

            // These are just strings, no parsing needed
            database_url: get_env("DATABASE_URL")?,
            rpc_url: get_env("RPC_URL")?,

            // Parse chain ID as u64 (unsigned 64-bit integer)
            chain_id: get_env("CHAIN_ID")?
                .parse()
                .map_err(|e: ParseIntError| e.to_string())?,

            // Keep as string - will be parsed later by PrivateKeySigner
            sequencer_private_key: get_env("SEQUENCER_PRIVATE_KEY")?,

            // Parse hex address string into Address type
            // Address::parse_checksummed handles "0x..." format
            // The second argument is the expected chain ID for checksum validation (None = skip)
            channel_manager: get_env("CHANNEL_MANAGER")?
                .parse()
                .map_err(|e| format!("invalid channel manager address: {}", e))?,
        })
    }
}

/// Helper function to get an environment variable
///
/// Returns `Result<String, String>`:
/// - `Ok(value)` if the variable exists and is not empty
/// - `Err(message)` if missing or empty
///
/// Why a helper function?
/// - `std::env::var` returns `Result<String, VarError>`
/// - We want to convert that to `Result<String, String>` with a nice message

fn get_env(key: &str) -> Result<String, String> {
    // std::env::var returns Result<String, VarError>
    // .map_err transforms the error type
    // |_| means "ignore the original error, use this message instead"
    var(key).map_err(|_| format!("Missing environment variable: {}", key))
}
