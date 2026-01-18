// model.rs - Data structures for the sequencer
//
// This file defines all the types we use throughout the application:
// - Internal state (ChannelState, RecipientBalance)
// - API request types (SeedChannelRequest, PayInChannelRequest, etc.)
// - API response types (ChannelView, PayInChannelResponse, etc.)
//
// We use serde for JSON serialization/deserialization.

use alloy::primitives::{Address, B256, U256};
use serde::{Deserialize, Serialize};

// =============================================================================
// INTERNAL STATE TYPES
// =============================================================================
// These types represent the actual state stored in memory and database.
// They use alloy primitive types for type safety.

/// Represents the current state of a payment channel
///
/// `#[derive(Debug, Clone)]`:
/// - `Debug`: allows `{:?}` formatting for logging
/// - `Clone`: allows creating copies of this struct
#[derive(Debug, Clone)]
pub struct ChannelState {
    /// Unique identifier for the channel (32-byte hash)
    pub channel_id: B256,

    /// Ethereum address of the channel owner (payer)
    pub owner: Address,

    /// Total balance deposited in the channel (in token wei)
    pub balance: U256,

    /// Unix timestamp when the channel expires
    pub expiry_ts: u64,

    /// Current sequence number (increments with each payment)
    pub sequence_number: u64,

    /// Latest voucher signature from the user
    pub user_signature: String,

    /// Latest co-signature from the sequencer
    pub sequencer_signature: String,

    /// Timestamp when signatures were created
    pub signature_timestamp: u64,

    /// List of recipients and their accumulated balances
    pub recipients: Vec<RecipientBalance>,
}

/// Tracks how much a recipient has received from a channel
#[derive(Debug, Clone)]
pub struct RecipientBalance {
    /// Ethereum address of the recipient
    pub recipient_address: Address,

    /// Total amount accumulated for this recipient
    pub balance: U256,

    /// Position in the recipients list (for ordering)
    pub position: i32,
}

// =============================================================================
// API REQUEST TYPES
// =============================================================================
// These types are deserialized from incoming JSON requests.
// We use String for addresses/amounts because JSON doesn't have native bigint.

/// Request to register a newly opened channel
///
/// `#[derive(Deserialize)]` - can be created from JSON
/// `#[serde(rename_all = "camelCase")]` - JSON uses camelCase, Rust uses snake_case
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedChannelRequest {
    /// Channel ID (hex string with 0x prefix)
    pub channel_id: String,

    /// Owner address (hex string with 0x prefix)
    pub owner: String,

    /// Initial balance (decimal string, e.g., "1000000")
    pub balance: String,

    /// Expiry timestamp (Unix seconds)
    pub expiry_timestamp: u64,
}

/// Optional fee information for a payment
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FeeForPayment {
    /// Address to receive the fee
    pub fee_destination_address: String,

    /// Fee amount in smallest units
    pub fee_amount: String,
}

/// Request to process a payment voucher
///
/// This is the main payment request - user signs a voucher
/// and sends it to the sequencer for validation and co-signing.
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PayInChannelRequest {
    /// Channel ID (hex string)
    pub channel_id: String,

    /// Payment amount (decimal string)
    pub amount: String,

    /// Recipient address (hex string)
    pub receiver: String,

    /// Sequence number (must be > current)
    pub sequence_number: u64,

    /// Timestamp when voucher was created
    pub timestamp: u64,

    /// EIP-712 signature from the channel owner
    pub user_signature: String,

    /// Optional description of what the payment is for
    pub purpose: Option<String>,

    /// Optional fee to deduct
    pub fee_for_payment: Option<FeeForPayment>,
}

/// Request to finalize (close) a channel on-chain
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FinalizeChannelRequest {
    /// Channel ID to finalize
    pub channel_id: String,
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================
// These types are serialized to JSON for outgoing responses.
// We use String for all values to ensure JSON compatibility.

/// JSON-friendly view of a channel (for API responses)
///
/// `#[derive(Serialize)]` - can be converted to JSON
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ChannelView {
    pub channel_id: String,
    pub owner: String,
    pub balance: String,
    pub expiry_timestamp: u64,
    pub sequence_number: u64,
    pub user_signature: String,
    pub sequencer_signature: String,
    pub signature_timestamp: u64,
    pub recipients: Vec<RecipientView>,
}

/// JSON-friendly view of a recipient balance
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecipientView {
    pub recipient_address: String,
    pub balance: String,
}

/// Response for pay-in-channel endpoint
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PayInChannelResponse {
    pub channel: ChannelView,
}

/// Response for finalize endpoint
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FinalizeChannelResponse {
    pub transaction_hash: String,
}

/// Response for channels-by-owner endpoint
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ChannelsByOwnerResponse {
    pub owner: String,
    pub channel_ids: Vec<String>,
}

// =============================================================================
// CONVERSION METHODS
// =============================================================================
// Methods to convert between internal state and API response types.

impl ChannelView {
    /// Convert internal ChannelState to API-friendly ChannelView
    ///
    /// `&ChannelState` = borrow the state (don't take ownership)
    /// `Self` = return type is ChannelView
    pub fn from_state(channel: &ChannelState) -> Self {
        Self {
            // format!("0x{:x}", value) formats as lowercase hex with 0x prefix
            channel_id: format!("0x{:x}", channel.channel_id),
            owner: format!("0x{:x}", channel.owner),
            balance: channel.balance.to_string(),
            expiry_timestamp: channel.expiry_ts,
            sequence_number: channel.sequence_number,
            user_signature: channel.user_signature.clone(),
            sequencer_signature: channel.sequencer_signature.clone(),
            signature_timestamp: channel.signature_timestamp,
            // Convert Vec<RecipientBalance> to Vec<RecipientView>
            // .iter() = iterate over references
            // .map(|r| ...) = transform each element
            // .collect() = collect into a Vec
            recipients: channel
                .recipients
                .iter()
                .map(|r| RecipientView {
                    recipient_address: format!("0x{:x}", r.recipient_address),
                    balance: r.balance.to_string(),
                })
                .collect(),
        }
    }
}
