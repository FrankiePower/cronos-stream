# Sequencer Service

The sequencer is an off-chain service that sits between clients and the smart contract. It's the "trusted middleman" that validates vouchers, co-signs them, and manages channel state.

## Architecture

```
┌──────────┐     voucher      ┌────────────┐     on-chain     ┌──────────────┐
│  Client  │ ───────────────▶ │ Sequencer  │ ───────────────▶ │ StreamChannel│
│ (Payer)  │                  │  Service   │                  │   Contract   │
└──────────┘                  └────────────┘                  └──────────────┘
     │                              │
     │ signs voucher                │ validates signature
     │ (EIP-712)                    │ co-signs voucher
     │                              │ stores state in DB
     │                              │ can finalize on-chain
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| POST /channel/seed | Register a new channel (after user opens on-chain) |
| GET /channel/:id | Get channel state |
| POST /validate | Validate a payment voucher (read-only, no state change) |
| POST /settle | Accept a payment voucher (updates state, co-signs) |
| POST /channel/finalize | Close channel on-chain (calls smart contract) |
| GET /channels/by-owner/:owner | List user's channels |

## File Structure

| File | Purpose |
|------|---------|
| main.rs | Entry point - loads config, connects DB, starts server |
| config.rs | Environment variable loading |
| error.rs | Custom error types |
| model.rs | Data structures (ChannelState, Request/Response types) |
| crypto.rs | EIP-712 signature verification and signing |
| db.rs | PostgreSQL persistence |
| service.rs | Business logic (validation, state updates) |
| handlers.rs | HTTP route handlers (thin layer) |

---

## Rust Concepts Guide (main.rs)

### 1. Module Declarations (Lines 3-9)

```rust
mod config;    // Configuration from environment
mod error;     // Custom error types
mod model;     // Data structures
mod crypto;    // EIP-712 signatures
mod db;        // Database operations
mod service;   // Business logic
mod handlers;  // HTTP route handlers
```

**What `mod` does:**
- `mod config;` tells Rust: "There's a file called `config.rs` (or folder `config/mod.rs`), include it as part of this project"
- It's like `import` in JS, but it **declares** that a module exists
- Without `mod`, Rust won't compile the file even if it exists

### 2. Standard Library Imports (Lines 11-12)

```rust
use std::net::SocketAddr;
use std::sync::Arc;
```

**`std::` = Rust's Standard Library** (built-in, always available)

- **`SocketAddr`**: Represents an IP address + port (like `0.0.0.0:3000`)
- **`Arc`**: Atomic Reference Counting - allows multiple owners of the same data across threads safely

### 3. External Crate Imports (Lines 14-17)

```rust
use alloy::providers::ProviderBuilder;
use alloy::signers::local::PrivateKeySigner;
use tokio::sync::RwLock;
use tracing::info;
```

**What each crate does:**
- **`alloy`**: Ethereum library (handles addresses, signatures, RPC calls)
- **`tokio`**: Async runtime (Rust needs explicit async support, unlike Node's built-in event loop)
- **`tracing`**: Structured logging (like winston/pino in Node)

**`RwLock`**: Read-Write Lock - allows multiple readers OR one writer at a time

### 4. Internal Module Imports (Lines 19-22)

```rust
use crate::config::Config;
use crate::db::{init_db, load_state};
use crate::handlers::create_router;
use crate::service::{fetch_sequencer_address, AppState};
```

**`crate::` = "from this project"**
- `crate::config::Config` means: "from our config.rs file, import the Config struct"
- Different from external crates like `alloy::` or `tokio::`

### 5. The Async Main Function (Lines 26-27)

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
```

**`#[tokio::main]`**:
- A macro that sets up the tokio async runtime
- Transforms this into a regular `fn main()` that starts tokio
- Without it, you can't use `await` in main

**`async fn`**:
- Marks the function as asynchronous
- Allows using `.await` inside

**`Result<(), Box<dyn std::error::Error>>`**:
- `Result<Ok, Err>` - the function returns either success or error
- `()` - on success, return nothing (like `void`)
- `Box<dyn std::error::Error>` - on error, return any error type
  - `Box` = heap-allocated (like putting in a box)
  - `dyn` = dynamic dispatch (any type that implements Error)

### 6. Loading Environment Variables (Lines 28-29)

```rust
dotenvy::dotenv().ok();
```

- Loads variables from `.env` file
- `.ok()` ignores errors (it's fine if `.env` doesn't exist)

### 7. Setting Up Logging (Lines 33-35)

```rust
tracing_subscriber::fmt()
    .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
    .init();
```

- Sets up terminal logging
- Log level controlled by `RUST_LOG` env var (e.g., `RUST_LOG=info cargo run`)
- `info!()`, `debug!()`, `error!()` macros print to terminal

### 8. Loading Configuration (Lines 37-39)

```rust
let config = Arc::new(Config::from_env()?);
let port = config.port;
```

- `Config::from_env()?` - load config from environment variables
- `?` - if error, return early from function
- `Arc::new()` - wrap in Arc for thread-safe sharing

### 9. Database Connection (Lines 43-46)

```rust
let db = sqlx::postgres::PgPoolOptions::new()
    .max_connections(5)
    .connect(&config.database_url)
    .await?;
```

- Creates a connection pool to PostgreSQL
- `.await` - wait for async operation to complete
- `&config.database_url` - borrow the URL string (don't take ownership)

### 10. Initialize Database & Load State (Lines 48-53)

```rust
init_db(&db).await?;
let channels = load_state(&db).await?;
info!("Loaded {} channels from database", channels.len());
```

- `init_db(&db)` - create tables if they don't exist
- `load_state(&db)` - load existing channel data into memory
- `info!()` - log message to terminal

### 11. Create RPC Provider (Lines 57-59)

```rust
let provider = ProviderBuilder::new()
    .on_http(config.rpc_url.parse()?);
let provider = Arc::new(provider);
```

- Creates connection to blockchain RPC
- Like `ethers.JsonRpcProvider` in JavaScript
- Wrapped in `Arc` for thread-safe sharing

### 12. Parse Sequencer Wallet (Lines 63-65)

```rust
let sequencer_signer: PrivateKeySigner = config.sequencer_private_key.parse()?;
let sequencer_address = sequencer_signer.address();
info!("Sequencer address: {}", sequencer_address);
```

- Parses private key string into a signer
- Gets the address from the private key
- This wallet will co-sign vouchers

### 13. Verify Against Smart Contract (Lines 69-80)

```rust
let onchain_sequencer = fetch_sequencer_address(
    provider.clone(),
    config.channel_manager,
).await?;

if onchain_sequencer != sequencer_address {
    return Err(format!(
        "Sequencer address mismatch! Config: {}, On-chain: {}",
        sequencer_address, onchain_sequencer
    ).into());
}
```

- Reads sequencer address from smart contract
- Compares with our wallet address
- Fails if they don't match (prevents misconfiguration)
- `.clone()` - create a copy of the Arc pointer (cheap operation)

### 14. Create Application State (Lines 85-91)

```rust
let state = AppState {
    db,
    channels: Arc::new(RwLock::new(channels)),
    config,
    provider,
    sequencer_signer,
};
```

- Bundle all shared resources into one struct
- `Arc<RwLock<HashMap>>` - thread-safe, lockable channel storage
- This state is passed to all HTTP handlers

### 15. Create Router & Start Server (Lines 94-102)

```rust
let app = create_router(state);
let addr = SocketAddr::from(([0, 0, 0, 0], port));
info!("Sequencer listening on {}", addr);

let listener = tokio::net::TcpListener::bind(addr).await?;
axum::serve(listener, app).await?;
```

- `create_router(state)` - creates HTTP routes with axum
- `SocketAddr::from(([0, 0, 0, 0], port))` - bind to all interfaces on specified port
- `TcpListener::bind` - start listening for connections
- `axum::serve` - start the HTTP server

### 16. Return Success (Line 104)

```rust
Ok(())
```

- Return success (empty tuple `()`)
- If we reach here, everything worked

---

## Complete Flow Summary

1. **Define modules** (`mod`) - tell Rust which files are part of the project
2. **Import items** (`use`) - bring specific types/functions into scope
3. **`#[tokio::main]`** - set up async runtime so we can use `await`
4. **Load .env** - read environment variables from file
5. **Set up logging** - configure terminal output (controlled by `RUST_LOG`)
6. **Load config** - parse environment variables into typed struct
7. **Connect to database** - create PostgreSQL connection pool
8. **Initialize tables** - create tables if they don't exist
9. **Load state** - read existing channels from DB into memory
10. **Create RPC provider** - connect to blockchain
11. **Parse sequencer wallet** - load private key for signing
12. **Verify wallet** - check our address matches the smart contract
13. **Create app state** - bundle all resources for handlers
14. **Create router** - set up HTTP routes
15. **Start server** - begin listening for requests

---

## Key Rust Concepts

| Concept | JavaScript Equivalent | Purpose |
|---------|----------------------|---------|
| `mod` | `import` (partial) | Declare a module exists |
| `use` | `import { x }` | Bring items into scope |
| `crate::` | `./` (relative import) | Reference current project |
| `Arc` | (none) | Thread-safe shared ownership |
| `RwLock` | (none) | Multiple readers OR one writer |
| `async/await` | `async/await` | Asynchronous operations |
| `Result<T, E>` | `Promise<T>` / try-catch | Error handling |
| `?` operator | `throw` (auto) | Propagate errors |
| `&` (borrow) | (none) | Reference without ownership |
| `.clone()` | spread operator | Create a copy |

---

## Running the Sequencer

```bash
### Setup
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your configuration (if needed).

### Run
```bash
cargo run
```
```
