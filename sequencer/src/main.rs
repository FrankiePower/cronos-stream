// main.rs - Entry point for the sequencer service

mod config; // Configuration from environment
mod crypto; // EIP-712 signatures
mod db; // Database operations
mod error; // Custom error types
mod handlers;
mod model; // Data structures
mod service; // Business logic // HTTP route handlers

use std::net::SocketAddr;
use std::sync::Arc;

use alloy::providers::ProviderBuilder;
use alloy::signers::local::PrivateKeySigner;
use tokio::sync::RwLock;
use tracing::info;

use crate::config::Config;
use crate::db::{init_db, load_state};
use crate::handlers::create_router;
use crate::service::{fetch_sequencer_address, AppState};

// #[tokio::main] is a macro that sets up the async runtime
// It transforms this into a regular fn main() that starts tokio
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load .env file (like dotenv in Node)
    dotenvy::dotenv().ok();

    // Initialize logging (like winston/pino in Node)
    // RUST_LOG=info cargo run  <- set log level via env var
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Load configuration from environment variables
    let config = Arc::new(Config::from_env()?);
    let port = config.port;

    // Connect to PostgreSQL
    // sqlx::PgPool is a connection pool (like pg-pool in Node)
    let db = sqlx::postgres::PgPoolOptions::new()
        .max_connections(5)
        .connect(&config.database_url)
        .await?;

    // Initialize database tables
    init_db(&db).await?;

    // Load existing channel state from DB into memory
    let channels = load_state(&db).await?;
    info!("Loaded {} channels from database", channels.len());

    // Create RPC provider to interact with blockchain
    // This is like ethers.JsonRpcProvider in JS
    // Create RPC provider to interact with blockchain
    // This is like ethers.JsonRpcProvider in JS
    let provider = ProviderBuilder::new()
        .disable_recommended_fillers()
        .connect_http(config.rpc_url.parse()?);
    let provider = Arc::new(provider);

    // Parse the sequencer's private key into a signer
    // This wallet will co-sign vouchers
    let sequencer_signer: PrivateKeySigner = config.sequencer_private_key.parse()?;
    let sequencer_address = sequencer_signer.address();
    info!("Sequencer address: {}", sequencer_address);

    // Verify our wallet matches what's set in the smart contract
    // This prevents misconfiguration
    let onchain_sequencer =
        fetch_sequencer_address(provider.clone(), config.channel_manager).await?;

    if onchain_sequencer != sequencer_address {
        return Err(format!(
            "Sequencer address mismatch! Config: {}, On-chain: {}",
            sequencer_address, onchain_sequencer
        )
        .into());
    }
    info!("Sequencer address verified against on-chain contract");

    // Create the application state
    // Arc = Atomic Reference Counting (shared ownership across threads)
    // RwLock = Read-Write Lock (multiple readers OR one writer)
    let state = AppState {
        db,
        channels: Arc::new(RwLock::new(channels)),
        config,
        provider,
        sequencer_signer,
    };

    // Create the HTTP router with all routes
    let app = create_router(state);

    // Bind to address and start serving
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    info!("Sequencer listening on {}", addr);

    // Start the server
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
