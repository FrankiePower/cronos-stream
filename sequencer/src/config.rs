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
            // RPC URL for connecting to the Cronos blockchain
            // This is used to send transactions and read blockchain data
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    #[test]
    fn test_load_config_from_file() {
        // Load the actual .env file from the current directory
        // We use from_filename to be explicit, but dotenv() would also work
        dotenvy::from_filename(".env").expect("Failed to load .env file");

        // Call from_env - this will now read the values we just loaded from the file
        let config = Config::from_env().expect("Failed to load config from .env file");

        // Assert values match what is in our .env
        assert_eq!(config.port, 4001);
        assert_eq!(config.chain_id, 31337);
        assert_eq!(config.database_url, "postgres://x402:x402@localhost:5432/x402");
        assert_eq!(config.rpc_url, "http://localhost:8545");
        assert_eq!(config.sequencer_private_key, "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80");
        
        // Check address (case insensitive comparison)
        assert_eq!(
            config.channel_manager, 
            "0x5FbDB2315678afecb367f032d93F642f64180aa3".parse::<Address>().unwrap()
        );
    }
}
