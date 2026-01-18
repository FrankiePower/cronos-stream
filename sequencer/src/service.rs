// service.rs - Business Logic
//
// This file contains the core business logic for the sequencer:
// - Seeding new channels (registering them after on-chain creation)
// - Processing payment vouchers (validate, update state, co-sign)
// - Finalizing channels (closing them on-chain)
// - Querying channel information
//
// The handlers (HTTP layer) call these functions.

use std::collections::HashMap;
use std::sync::Arc;

use alloy::network::{Ethereum, EthereumWallet};
use alloy::primitives::{Address, U256};
use alloy::providers::{ProviderBuilder, RootProvider};
use alloy::signers::local::PrivateKeySigner;
use alloy::sol;
use sqlx::PgPool;
use tokio::sync::RwLock;
use tracing::info;

use crate::config::Config;
use crate::crypto::{
    parse_address, parse_b256, parse_u256, recover_signature, sign_update, validate_timestamp,
};
use crate::db::save_channel;
use crate::error::AppError;
use crate::model::{
    ChannelState, ChannelView, ChannelsByOwnerResponse, FinalizeChannelRequest,
    FinalizeChannelResponse, PayInChannelRequest, PayInChannelResponse, RecipientBalance,
    SeedChannelRequest,
};

// =============================================================================
// APPLICATION STATE
// =============================================================================

/// Shared state passed to all handlers
///
/// `#[derive(Clone)]` - can be cloned (but Arc/RwLock make this cheap)
#[derive(Clone)]
pub struct AppState {
    /// Database connection pool
    pub db: PgPool,

    /// In-memory channel state
    /// Arc = shared ownership across threads
    /// RwLock = multiple readers OR one writer
    /// HashMap = channel_id -> ChannelState
    pub channels: Arc<RwLock<HashMap<String, ChannelState>>>,

    /// Configuration loaded from environment
    pub config: Arc<Config>,

    /// RPC provider for blockchain calls
    pub provider: Arc<RootProvider>,

    /// Sequencer's signing wallet
    pub sequencer_signer: PrivateKeySigner,
}

// =============================================================================
// SOLIDITY CONTRACT INTERFACES
// =============================================================================
// alloy's sol! macro generates Rust types from Solidity interfaces.
// This gives us type-safe contract interactions.

sol! {
    /// Interface for reading sequencer address from contract
    #[sol(rpc)]
    contract IStreamChannel {
        function sequencer() external view returns (address);
        function getUserChannelLength(address owner) external view returns (uint256);
        function userChannels(address owner, uint256 index) external view returns (bytes32);
        function finalCloseBySequencer(
            bytes32 channelId,
            uint256 sequenceNumber,
            uint256 timestamp,
            address[] calldata recipients,
            uint256[] calldata amounts,
            bytes calldata userSignature
        ) external;
    }
}

// =============================================================================
// STARTUP FUNCTIONS
// =============================================================================

/// Fetch the sequencer address from the smart contract
///
/// Called at startup to verify our wallet matches what's on-chain.
pub async fn fetch_sequencer_address(
    provider: Arc<RootProvider>,
    channel_manager: Address,
) -> Result<Address, AppError> {
    // Create a contract instance
    let contract = IStreamChannel::new(channel_manager, provider);

    // Call the sequencer() view function
    let result = contract
        .sequencer()
        .call()
        .await
        .map_err(|e| AppError::ContractCall(format!("failed to fetch sequencer: {}", e)))?;

    Ok(Address::from(result.0))
}

// =============================================================================
// CHANNEL OPERATIONS
// =============================================================================

/// Register a newly created channel
///
/// After a user opens a channel on-chain, they call this endpoint
/// to register it with the sequencer. The sequencer doesn't verify
/// on-chain state here (trust the user), but stores the initial state.
pub async fn seed_channel(
    state: &AppState,
    payload: SeedChannelRequest,
) -> Result<ChannelView, AppError> {
    // Parse the input values from strings to typed values
    let channel_id = parse_b256(&payload.channel_id)?;
    let owner = parse_address(&payload.owner)?;
    let balance = parse_u256(&payload.balance)?;

    // Create initial channel state
    // sequence_number starts at 0, no signatures yet
    let channel_state = ChannelState {
        channel_id,
        owner,
        balance,
        expiry_ts: payload.expiry_timestamp,
        sequence_number: 0,
        user_signature: String::new(),
        sequencer_signature: String::new(),
        signature_timestamp: 0,
        recipients: Vec::new(),
    };

    // Save to database
    save_channel(&state.db, &channel_state).await?;

    // Update in-memory state
    // .write().await acquires write lock (blocks other writers AND readers)
    let mut channels = state.channels.write().await;
    channels.insert(payload.channel_id.clone(), channel_state);

    // Return the channel view
    let view = ChannelView::from_state(channels.get(&payload.channel_id).unwrap());
    Ok(view)
}

/// Get channel state by ID
pub async fn get_channel(state: &AppState, channel_id: String) -> Result<ChannelView, AppError> {
    // .read().await acquires read lock (allows other readers, blocks writers)
    let channels = state.channels.read().await;

    let channel = channels
        .get(&channel_id)
        .ok_or_else(|| AppError::ChannelNotFound(channel_id))?;

    Ok(ChannelView::from_state(channel))
}

/// Validate a payment voucher (read-only, no state change)
///
/// This lets users check if a voucher would be accepted before
/// committing to it. Useful for UX.
pub async fn validate_pay_in_channel(
    state: &AppState,
    payload: PayInChannelRequest,
) -> Result<PayInChannelResponse, AppError> {
    let channels = state.channels.read().await;
    let channel = channels
        .get(&payload.channel_id)
        .ok_or_else(|| AppError::ChannelNotFound(payload.channel_id.clone()))?;

    // Check if this is a replay of the current state
    if payload.sequence_number == channel.sequence_number {
        if payload.user_signature == channel.user_signature
            && payload.timestamp == channel.signature_timestamp
        {
            // Idempotent: return current state
            return Ok(PayInChannelResponse {
                channel: ChannelView::from_state(channel),
            });
        }
        return Err(AppError::InvalidSequenceNumber {
            expected: channel.sequence_number,
            actual: payload.sequence_number,
        });
    }

    // Sequence number must increment by exactly 1
    if payload.sequence_number != channel.sequence_number + 1 {
        return Err(AppError::InvalidSequenceNumber {
            expected: channel.sequence_number + 1,
            actual: payload.sequence_number,
        });
    }

    // Compute what the next state would be (validates signature, etc.)
    let updated = compute_next_state(channel, &payload, state).await?;

    Ok(PayInChannelResponse {
        channel: ChannelView::from_state(&updated),
    })
}

/// Process a payment voucher (updates state, co-signs)
///
/// This is the main payment endpoint. The user sends a signed voucher,
/// we validate it, update state, co-sign, and save to DB.
pub async fn settle(
    state: &AppState,
    payload: PayInChannelRequest,
) -> Result<PayInChannelResponse, AppError> {
    let channel_id = parse_b256(&payload.channel_id)?;

    // Acquire write lock (exclusive access)
    let mut channels = state.channels.write().await;
    let channel = channels
        .get_mut(&payload.channel_id)
        .ok_or_else(|| AppError::ChannelNotFound(payload.channel_id.clone()))?;

    // Check for replay of current state (idempotent)
    if payload.sequence_number == channel.sequence_number {
        if payload.user_signature == channel.user_signature
            && payload.timestamp == channel.signature_timestamp
        {
            return Ok(PayInChannelResponse {
                channel: ChannelView::from_state(channel),
            });
        }
        return Err(AppError::InvalidSequenceNumber {
            expected: channel.sequence_number,
            actual: payload.sequence_number,
        });
    }

    // Sequence number must increment by exactly 1
    if payload.sequence_number != channel.sequence_number + 1 {
        return Err(AppError::InvalidSequenceNumber {
            expected: channel.sequence_number + 1,
            actual: payload.sequence_number,
        });
    }

    // Log the purpose if provided
    if let Some(purpose) = payload.purpose.as_deref() {
        info!(
            purpose = %purpose,
            channel_id = %format!("0x{:x}", channel_id),
            "settle purpose"
        );
    }

    // Compute the updated state (validates signature)
    let mut updated = compute_next_state(channel, &payload, state).await?;

    // Co-sign with sequencer's wallet
    let sequencer_signature = sign_update(
        &state.sequencer_signer,
        updated.channel_id,
        updated.sequence_number,
        updated.signature_timestamp,
        &updated.recipients,
        state.config.chain_id,
        state.config.channel_manager,
    )
    .await?;

    updated.sequencer_signature = sequencer_signature;

    // Update in-memory state
    *channel = updated;

    // Persist to database
    save_channel(&state.db, channel).await?;

    Ok(PayInChannelResponse {
        channel: ChannelView::from_state(channel),
    })
}

/// Finalize (close) a channel on-chain
///
/// Calls the smart contract to distribute funds to recipients.
/// Requires valid user signature.
pub async fn finalize_channel(
    state: &AppState,
    payload: FinalizeChannelRequest,
) -> Result<FinalizeChannelResponse, AppError> {
    let channels = state.channels.read().await;
    let channel = channels
        .get(&payload.channel_id)
        .ok_or_else(|| AppError::ChannelNotFound(payload.channel_id.clone()))?;

    // Must have signatures to finalize
    if channel.user_signature.is_empty() {
        return Err(AppError::Internal("channel has no user signature".into()));
    }
    if channel.signature_timestamp == 0 {
        return Err(AppError::Internal(
            "channel has no signature timestamp".into(),
        ));
    }

    // Validate the timestamp
    validate_timestamp(channel.signature_timestamp, channel.expiry_ts)?;

    // Verify user signature
    let recovered = recover_signature(
        channel.channel_id,
        channel.sequence_number,
        channel.signature_timestamp,
        &channel.recipients,
        state.config.chain_id,
        state.config.channel_manager,
        &channel.user_signature,
    )
    .await?;

    if recovered != channel.owner {
        return Err(AppError::InvalidSignature {
            expected: format!("0x{:x}", channel.owner),
            actual: format!("0x{:x}", recovered),
        });
    }

    // Prepare contract call parameters
    let recipients: Vec<Address> = channel
        .recipients
        .iter()
        .map(|r| r.recipient_address)
        .collect();
    let amounts: Vec<U256> = channel.recipients.iter().map(|r| r.balance).collect();
    let signature_bytes = parse_signature_bytes(&channel.user_signature)?;

    // Create contract instance with signer
    // We create a new provider with the wallet attached for this transaction
    let wallet = EthereumWallet::from(state.sequencer_signer.clone());
    let provider = ProviderBuilder::<_, _, Ethereum>::new()
        .wallet(wallet)
        .connect_http(
            state
                .config
                .rpc_url
                .parse()
                .map_err(|e| AppError::Internal(format!("invalid rpc url: {}", e)))?,
        );

    let contract = IStreamChannel::new(state.config.channel_manager, provider);

    // Build and send the transaction
    let call = contract.finalCloseBySequencer(
        channel.channel_id,
        U256::from(channel.sequence_number),
        U256::from(channel.signature_timestamp),
        recipients,
        amounts,
        signature_bytes.into(),
    );

    // Send the transaction (signs automatically with the attached wallet)
    let pending_tx = call
        .send()
        .await
        .map_err(|e| AppError::ContractCall(format!("transaction failed: {}", e)))?;

    let tx_hash = pending_tx
        .watch()
        .await
        .map_err(|e| AppError::ContractCall(format!("transaction confirmation failed: {}", e)))?;

    Ok(FinalizeChannelResponse {
        transaction_hash: format!("0x{:x}", tx_hash),
    })
}

/// List all channels owned by an address
pub async fn list_channels_by_owner(
    state: &AppState,
    owner: String,
) -> Result<ChannelsByOwnerResponse, AppError> {
    let owner_address = parse_address(&owner)?;
    let contract = IStreamChannel::new(state.config.channel_manager, state.provider.clone());

    // Get the number of channels
    let length = contract
        .getUserChannelLength(owner_address)
        .call()
        .await
        .map_err(|e| AppError::ContractCall(format!("failed to get channel length: {}", e)))?;

    // Fetch each channel ID
    let mut channel_ids = Vec::with_capacity(length.to::<usize>());
    for index in 0..length.to::<u64>() {
        let channel_id = contract
            .userChannels(owner_address, U256::from(index))
            .call()
            .await
            .map_err(|e| AppError::ContractCall(format!("failed to get channel: {}", e)))?;
        channel_ids.push(format!("0x{}", hex::encode(channel_id)));
    }

    Ok(ChannelsByOwnerResponse {
        owner: format!("0x{:x}", owner_address),
        channel_ids,
    })
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/// Compute the next channel state after a payment
///
/// This validates the voucher and computes what the state would be
/// if we accept it. Doesn't modify anything.
async fn compute_next_state(
    channel: &ChannelState,
    payload: &PayInChannelRequest,
    state: &AppState,
) -> Result<ChannelState, AppError> {
    let receiver = parse_address(&payload.receiver)?;
    let amount = parse_u256(&payload.amount)?;

    // Parse optional fee
    let fee = payload
        .fee_for_payment
        .as_ref()
        .map(|fee| -> Result<(Address, U256), AppError> {
            let fee_address = parse_address(&fee.fee_destination_address)?;
            let fee_amount = parse_u256(&fee.fee_amount)?;
            Ok((fee_address, fee_amount))
        })
        .transpose()?; // transpose: Option<Result<T, E>> -> Result<Option<T>, E>

    // Amount must be positive
    if amount.is_zero() {
        return Err(AppError::InsufficientBalance);
    }

    // Validate timestamp
    validate_timestamp(payload.timestamp, channel.expiry_ts)?;

    // Clone recipients and add new amounts
    let mut recipients = channel.recipients.clone();
    add_amount(&mut recipients, receiver, amount);
    if let Some((fee_address, fee_amount)) = fee {
        add_amount(&mut recipients, fee_address, fee_amount);
    }

    // Check total doesn't exceed channel balance
    let total: U256 = recipients.iter().fold(U256::ZERO, |acc, r| acc + r.balance);
    if total > channel.balance {
        return Err(AppError::BalanceOverflow);
    }

    // Verify user signature
    let recovered = recover_signature(
        channel.channel_id,
        payload.sequence_number,
        payload.timestamp,
        &recipients,
        state.config.chain_id,
        state.config.channel_manager,
        &payload.user_signature,
    )
    .await?;

    if recovered != channel.owner {
        return Err(AppError::InvalidSignature {
            expected: format!("0x{:x}", channel.owner),
            actual: format!("0x{:x}", recovered),
        });
    }

    // Create updated state
    let mut updated = channel.clone();
    updated.sequence_number = payload.sequence_number;
    updated.user_signature = payload.user_signature.clone();
    updated.sequencer_signature = String::new();
    updated.signature_timestamp = payload.timestamp;
    updated.recipients = recipients;

    Ok(updated)
}

/// Add amount to a recipient's balance (or create new entry)
fn add_amount(recipients: &mut Vec<RecipientBalance>, address: Address, amount: U256) {
    if amount.is_zero() {
        return;
    }

    // Check if recipient already exists
    if let Some(existing) = recipients
        .iter_mut()
        .find(|r| r.recipient_address == address)
    {
        existing.balance += amount;
        return;
    }

    // Add new recipient
    let position = recipients.len() as i32;
    recipients.push(RecipientBalance {
        recipient_address: address,
        balance: amount,
        position,
    });
}

/// Parse signature hex string to bytes
fn parse_signature_bytes(signature: &str) -> Result<Vec<u8>, AppError> {
    let trimmed = signature.strip_prefix("0x").unwrap_or(signature);
    hex::decode(trimmed)
        .map_err(|e| AppError::MalformedSignature(format!("invalid signature hex: {}", e)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloy::primitives::{address, b256};
    use alloy::signers::local::PrivateKeySigner;

    #[tokio::test]
    async fn test_signature_recovery_logic() {
        // 1. Setup keys
        let user_signer = PrivateKeySigner::random();
        let user_address = user_signer.address();

        // 2. Mock Channel State
        let channel_id = b256!("0000000000000000000000000000000000000000000000000000000000000001");
        let sequence_number = 1;
        let timestamp = 1234567890;
        let recipients = vec![];
        let chain_id = 31337;
        let channel_manager = address!("0000000000000000000000000000000000000002");

        // 3. Create Signature using the same helper as `sign_update` but for user
        // We reuse `sign_update` logic concept from `crypto.rs` (but we need to call it or replicate it)
        // Accessing crypto is possible since it's in the crate.
        use crate::crypto::sign_update;

        let signature_hex = sign_update(
            &user_signer,
            channel_id,
            sequence_number,
            timestamp,
            &recipients,
            chain_id,
            channel_manager,
        )
        .await
        .expect("signing failed");

        // 4. Test Recovery
        let recovered = recover_signature(
            channel_id,
            sequence_number,
            timestamp,
            &recipients,
            chain_id,
            channel_manager,
            &signature_hex,
        )
        .await
        .expect("recovery failed");

        assert_eq!(
            recovered, user_address,
            "Recovered address should match signer"
        );
    }
}
