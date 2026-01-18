// db.rs - Database Operations
//
// This file handles all PostgreSQL interactions:
// - Creating tables on startup
// - Loading channel state into memory
// - Saving channel updates
//
// We use sqlx for async database operations.
// Unlike ORMs, sqlx validates queries at compile time against your DB.

use sqlx::{PgPool, Row};
use std::collections::HashMap;

use crate::crypto::{parse_address, parse_b256, parse_u256};
use crate::model::{ChannelState, RecipientBalance};

// =============================================================================
// DATABASE INITIALIZATION
// =============================================================================

/// Create database tables if they don't exist
///
/// Called once at startup to ensure the schema is ready.
/// `IF NOT EXISTS` makes this safe to run multiple times.
pub async fn init_db(db: &PgPool) -> Result<(), sqlx::Error> {
    // Create the main channels table
    // Each channel has: id, owner, balance, expiry, sequence, signatures, timestamp
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS channels (\
            channel_id TEXT PRIMARY KEY,\
            owner TEXT NOT NULL,\
            balance TEXT NOT NULL,\
            expiry_ts BIGINT NOT NULL,\
            sequence_number BIGINT NOT NULL,\
            user_signature TEXT NOT NULL,\
            sequencer_signature TEXT NOT NULL,\
            signature_timestamp BIGINT NOT NULL\
        )",
    )
    .execute(db)
    .await?;

    // Create recipients table for tracking per-recipient balances
    // Foreign key ensures recipients are deleted when channel is deleted
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS recipients (\
            channel_id TEXT NOT NULL,\
            recipient_address TEXT NOT NULL,\
            balance TEXT NOT NULL,\
            position INT NOT NULL,\
            PRIMARY KEY (channel_id, recipient_address),\
            FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE\
        )",
    )
    .execute(db)
    .await?;

    Ok(())
}

// =============================================================================
// LOADING STATE
// =============================================================================

/// Load all channel state from database into memory
///
/// Returns a HashMap where:
/// - Key: channel_id as hex string (e.g., "0x1234...")
/// - Value: ChannelState struct with all channel data
///
/// Called at startup to restore state after restart.
pub async fn load_state(db: &PgPool) -> Result<HashMap<String, ChannelState>, sqlx::Error> {
    // HashMap is like JavaScript's Map or object
    let mut map = HashMap::new();

    // Fetch all channels
    let rows = sqlx::query(
        "SELECT channel_id, owner, balance, expiry_ts, sequence_number, \
         user_signature, sequencer_signature, signature_timestamp \
         FROM channels",
    )
    .fetch_all(db)
    .await?;

    // Process each channel row
    for row in rows {
        // Extract values from the row
        // try_get returns Result, so we use ? to propagate errors
        let channel_id_str: String = row.try_get("channel_id")?;
        let owner_str: String = row.try_get("owner")?;
        let balance_str: String = row.try_get("balance")?;
        let expiry_ts: i64 = row.try_get("expiry_ts")?;
        let sequence_number: i64 = row.try_get("sequence_number")?;
        let user_signature: String = row.try_get("user_signature")?;
        let sequencer_signature: String = row.try_get("sequencer_signature")?;
        let signature_timestamp: i64 = row.try_get("signature_timestamp")?;

        // Fetch recipients for this channel
        let recipients_rows = sqlx::query(
            "SELECT recipient_address, balance, position \
             FROM recipients \
             WHERE channel_id = $1 \
             ORDER BY position",
        )
        .bind(&channel_id_str) // $1 parameter binding (prevents SQL injection)
        .fetch_all(db)
        .await?;

        // Convert recipient rows to RecipientBalance structs
        let mut recipients = Vec::new();
        for recipient_row in recipients_rows {
            let address_str: String = recipient_row.try_get("recipient_address")?;
            let balance_str: String = recipient_row.try_get("balance")?;
            let position: i32 = recipient_row.try_get("position")?;

            recipients.push(RecipientBalance {
                // Parse strings back to typed values
                // unwrap_or_default() uses zero/empty if parsing fails
                recipient_address: parse_address(&address_str).unwrap_or_default(),
                balance: parse_u256(&balance_str).unwrap_or_default(),
                position,
            });
        }

        // Create the channel state struct
        let channel_state = ChannelState {
            channel_id: parse_b256(&channel_id_str).unwrap_or_default(),
            owner: parse_address(&owner_str).unwrap_or_default(),
            balance: parse_u256(&balance_str).unwrap_or_default(),
            expiry_ts: expiry_ts as u64,
            sequence_number: sequence_number as u64,
            user_signature,
            sequencer_signature,
            signature_timestamp: signature_timestamp as u64,
            recipients,
        };

        // Insert into the HashMap
        // channel_id_str is the key, channel_state is the value
        map.insert(channel_id_str, channel_state);
    }

    Ok(map)
}

// =============================================================================
// SAVING STATE
// =============================================================================

/// Save or update a channel in the database
///
/// Uses UPSERT pattern (INSERT ... ON CONFLICT ... DO UPDATE)
/// to handle both new channels and updates to existing ones.
pub async fn save_channel(db: &PgPool, channel: &ChannelState) -> Result<(), sqlx::Error> {
    // Upsert the channel record
    // ON CONFLICT = if channel_id already exists, update instead of insert
    sqlx::query(
        "INSERT INTO channels \
            (channel_id, owner, balance, expiry_ts, sequence_number, \
             user_signature, sequencer_signature, signature_timestamp) \
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8) \
         ON CONFLICT (channel_id) DO UPDATE SET \
            owner = EXCLUDED.owner, \
            balance = EXCLUDED.balance, \
            expiry_ts = EXCLUDED.expiry_ts, \
            sequence_number = EXCLUDED.sequence_number, \
            user_signature = EXCLUDED.user_signature, \
            sequencer_signature = EXCLUDED.sequencer_signature, \
            signature_timestamp = EXCLUDED.signature_timestamp",
    )
    // Bind parameters to prevent SQL injection
    // format!("0x{:x}", ...) converts typed values to hex strings
    .bind(format!("0x{:x}", channel.channel_id))
    .bind(format!("0x{:x}", channel.owner))
    .bind(channel.balance.to_string())
    .bind(channel.expiry_ts as i64)
    .bind(channel.sequence_number as i64)
    .bind(&channel.user_signature)
    .bind(&channel.sequencer_signature)
    .bind(channel.signature_timestamp as i64)
    .execute(db)
    .await?;

    // Upsert each recipient
    for recipient in &channel.recipients {
        sqlx::query(
            "INSERT INTO recipients (channel_id, recipient_address, balance, position) \
             VALUES ($1, $2, $3, $4) \
             ON CONFLICT (channel_id, recipient_address) DO UPDATE SET \
                balance = EXCLUDED.balance, \
                position = EXCLUDED.position",
        )
        .bind(format!("0x{:x}", channel.channel_id))
        .bind(format!("0x{:x}", recipient.recipient_address))
        .bind(recipient.balance.to_string())
        .bind(recipient.position)
        .execute(db)
        .await?;
    }

    Ok(())
}