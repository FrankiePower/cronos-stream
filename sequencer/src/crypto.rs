// crypto.rs - EIP-712 Signature Handling
//
// This file handles cryptographic operations:
// - Parsing addresses, hashes, and uint256 values from strings
// - Creating EIP-712 typed data hashes
// - Recovering signer addresses from signatures
// - Signing messages with the sequencer's wallet
//
// EIP-712 is a standard for signing typed data in Ethereum.
// It provides better security than signing raw messages.

use alloy::primitives::{keccak256, Address, B256, U256};
use alloy::signers::{local::PrivateKeySigner, Signature, Signer};
use std::str::FromStr;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use crate::error::AppError;
use crate::model::RecipientBalance;

// =============================================================================
// CONSTANTS
// =============================================================================
// These must match the values in the smart contract exactly.

/// Domain name for EIP-712 (identifies the application)
const DOMAIN_NAME: &str = "StreamChannel";

/// Domain version for EIP-712
const DOMAIN_VERSION: &str = "1";

// =============================================================================
// PARSING FUNCTIONS
// =============================================================================
// Convert hex strings from JSON into typed values.

/// Parse an Ethereum address from a hex string (with or without 0x prefix)
///
/// `&str` = borrowed string slice (input)
/// `Result<Address, AppError>` = either parsed Address or error
pub fn parse_address(input: &str) -> Result<Address, AppError> {
    // Address::from_str tries to parse the string
    // .map_err transforms the error if parsing fails
    Address::from_str(input)
        .map_err(|_| AppError::MalformedSignature(format!("invalid address: {}", input)))
}

/// Parse a 32-byte hash (channel ID) from hex string
pub fn parse_b256(input: &str) -> Result<B256, AppError> {
    B256::from_str(input)
        .map_err(|_| AppError::MalformedSignature(format!("invalid channel id: {}", input)))
}

/// Parse a U256 (big integer) from decimal string
pub fn parse_u256(input: &str) -> Result<U256, AppError> {
    U256::from_str(input)
        .map_err(|_| AppError::MalformedSignature(format!("invalid uint256: {}", input)))
}

// =============================================================================
// TIMESTAMP VALIDATION
// =============================================================================

/// Validate that a voucher timestamp is reasonable
///
/// Rules:
/// - Timestamp cannot be more than 15 minutes in the future
/// - Timestamp cannot be after channel expiry
pub fn validate_timestamp(timestamp: u64, expiry_ts: u64) -> Result<(), AppError> {
    // Get current Unix timestamp
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or(Duration::from_secs(0))
        .as_secs();

    // Allow up to 15 minutes in the future (for clock drift)
    let max_future = now + 15 * 60;

    if timestamp > max_future {
        return Err(AppError::Internal(
            "timestamp is too far in the future".into(),
        ));
    }

    if timestamp > expiry_ts {
        return Err(AppError::ChannelExpired);
    }

    Ok(())
}

// =============================================================================
// SIGNATURE RECOVERY
// =============================================================================

/// Recover the signer's address from an EIP-712 signature
///
/// This is how we verify that the user actually signed the voucher.
/// We reconstruct the same hash they should have signed, then
/// mathematically recover who signed it.
pub async fn recover_signature(
    channel_id: B256,
    sequence_number: u64,
    timestamp: u64,
    recipients: &[RecipientBalance],
    chain_id: u64,
    verifying_contract: Address,
    signature: &str,
) -> Result<Address, AppError> {
    // First, reconstruct the EIP-712 digest that was signed
    let digest = channel_update_digest(
        channel_id,
        sequence_number,
        timestamp,
        recipients,
        chain_id,
        verifying_contract,
    );

    // Parse the signature string into bytes
    // Signatures are 65 bytes: r (32) + s (32) + v (1)
    let sig_bytes = parse_signature_bytes(signature)?;

    // Create a Signature from the components
    let sig = Signature::try_from(sig_bytes.as_slice())
        .map_err(|e| AppError::MalformedSignature(format!("invalid signature format: {}", e)))?;

    // Recover the signer's address from the signature
    sig.recover_address_from_prehash(&digest)
        .map_err(|e| AppError::MalformedSignature(format!("signature recovery failed: {}", e)))
}

/// Parse a hex signature string into bytes
fn parse_signature_bytes(signature: &str) -> Result<Vec<u8>, AppError> {
    // Remove 0x prefix if present
    let sig_hex = signature.strip_prefix("0x").unwrap_or(signature);

    // Decode hex to bytes
    hex::decode(sig_hex)
        .map_err(|e| AppError::MalformedSignature(format!("invalid signature hex: {}", e)))
}

// =============================================================================
// SIGNING
// =============================================================================

/// Sign a channel update with the sequencer's wallet
///
/// This creates the co-signature that makes a voucher valid.
/// Both user and sequencer signatures are required to close a channel.
pub async fn sign_update(
    wallet: &PrivateKeySigner,
    channel_id: B256,
    sequence_number: u64,
    timestamp: u64,
    recipients: &[RecipientBalance],
    chain_id: u64,
    verifying_contract: Address,
) -> Result<String, AppError> {
    // Create the EIP-712 digest
    let digest = channel_update_digest(
        channel_id,
        sequence_number,
        timestamp,
        recipients,
        chain_id,
        verifying_contract,
    );

    // Sign the digest with the sequencer's private key
    let signature = wallet
        .sign_hash(&digest)
        .await
        .map_err(|e| AppError::Internal(format!("sequencer signing failed: {}", e)))?;

    // Convert to hex string with 0x prefix
    Ok(format!("0x{}", hex::encode(signature.as_bytes())))
}

// =============================================================================
// EIP-712 DIGEST COMPUTATION
// =============================================================================
// EIP-712 creates a unique hash of typed structured data.
// The format is: keccak256("\x19\x01" || domainSeparator || structHash)

/// Compute the EIP-712 digest for a channel update
///
/// This hash is what gets signed. It includes:
/// - Domain separator (identifies this app and chain)
/// - Struct hash (the actual channel update data)
fn channel_update_digest(
    channel_id: B256,
    sequence_number: u64,
    timestamp: u64,
    recipients: &[RecipientBalance],
    chain_id: u64,
    verifying_contract: Address,
) -> B256 {
    // Hash the recipients list
    let recipients_hash = hash_addresses(recipients.iter().map(|r| r.recipient_address));
    let amounts_hash = hash_u256s(recipients.iter().map(|r| r.balance));

    // Type hash identifies the struct type being signed
    // This string must match exactly what the smart contract expects
    let type_hash = keccak256(
        b"ChannelData(bytes32 channelId,uint256 sequenceNumber,uint256 timestamp,address[] recipients,uint256[] amounts)",
    );

    // Encode the struct data
    // Each field is 32 bytes, concatenated together
    let mut struct_data = Vec::with_capacity(6 * 32);
    struct_data.extend_from_slice(type_hash.as_slice());
    struct_data.extend_from_slice(channel_id.as_slice());
    struct_data.extend_from_slice(&pad_u256(U256::from(sequence_number)));
    struct_data.extend_from_slice(&pad_u256(U256::from(timestamp)));
    struct_data.extend_from_slice(recipients_hash.as_slice());
    struct_data.extend_from_slice(amounts_hash.as_slice());

    let struct_hash = keccak256(&struct_data);

    // Get the domain separator
    let domain_separator = domain_separator(chain_id, verifying_contract);

    // Final digest: 0x19 0x01 || domainSeparator || structHash
    let mut digest_input = Vec::with_capacity(2 + 32 + 32);
    digest_input.extend_from_slice(&[0x19, 0x01]);
    digest_input.extend_from_slice(domain_separator.as_slice());
    digest_input.extend_from_slice(struct_hash.as_slice());

    keccak256(&digest_input)
}

/// Compute the EIP-712 domain separator
///
/// This identifies the application and chain to prevent
/// signatures from being replayed on different chains/contracts.
fn domain_separator(chain_id: u64, verifying_contract: Address) -> B256 {
    // Type hash for the domain struct
    let domain_type_hash = keccak256(
        b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)",
    );

    // Hash the domain name and version strings
    let name_hash = keccak256(DOMAIN_NAME.as_bytes());
    let version_hash = keccak256(DOMAIN_VERSION.as_bytes());

    // Encode domain data
    let mut encoded = Vec::with_capacity(5 * 32);
    encoded.extend_from_slice(domain_type_hash.as_slice());
    encoded.extend_from_slice(name_hash.as_slice());
    encoded.extend_from_slice(version_hash.as_slice());
    encoded.extend_from_slice(&pad_u256(U256::from(chain_id)));
    // Address is 20 bytes, needs to be left-padded to 32 bytes
    encoded.extend_from_slice(&[0u8; 12]); // 12 zero bytes
    encoded.extend_from_slice(verifying_contract.as_slice());

    keccak256(&encoded)
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/// Hash a list of addresses (for EIP-712 array encoding)
fn hash_addresses<I>(iter: I) -> B256
where
    I: IntoIterator<Item = Address>,
{
    let mut bytes = Vec::new();
    for address in iter {
        // Each address is left-padded to 32 bytes
        bytes.extend_from_slice(&[0u8; 12]);
        bytes.extend_from_slice(address.as_slice());
    }
    keccak256(&bytes)
}

/// Hash a list of U256 values (for EIP-712 array encoding)
fn hash_u256s<I>(iter: I) -> B256
where
    I: IntoIterator<Item = U256>,
{
    let mut bytes = Vec::new();
    for value in iter {
        bytes.extend_from_slice(&value.to_be_bytes::<32>());
    }
    keccak256(&bytes)
}

/// Pad a U256 to 32 bytes (big-endian)
fn pad_u256(value: U256) -> [u8; 32] {
    value.to_be_bytes::<32>()
}
