// error.rs - Custom error types for the sequencer

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    // =========================================================================
    // Channel Errors - problems with payment channels
    // =========================================================================
    /// Channel doesn't exist in our database
    #[error("Channel not found: {0}")]
    ChannelNotFound(String),

    /// Channel has expired (past its expiry timestamp)
    #[error("Channel expired")]
    ChannelExpired,

    /// Channel doesn't have enough balance for the payment
    #[error("Insufficient channel balance")]
    InsufficientBalance,

    // =========================================================================
    // Signature Errors - problems with EIP-712 signatures
    // =========================================================================
    /// The signature doesn't match the expected signer
    #[error("Invalid signature: expected {expected}, got {actual}")]
    InvalidSignature { expected: String, actual: String },

    /// The signature bytes couldn't be parsed
    #[error("Malformed signature: {0}")]
    MalformedSignature(String),

    // =========================================================================
    // Voucher Errors - problems with payment vouchers
    // =========================================================================
    /// Voucher sequence number must be higher than current
    #[error("Invalid sequence number: expected > {expected}, got {actual}")]
    InvalidSequenceNumber { expected: u64, actual: u64 },

    /// Total recipient balances exceed channel balance
    #[error("Recipient balances exceed channel balance")]
    BalanceOverflow,

    // =========================================================================
    // Database Errors - problems with PostgreSQL
    // =========================================================================
    /// Database operation failed
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    // =========================================================================
    // Blockchain Errors - problems with RPC calls
    // =========================================================================
    /// Failed to call smart contract
    #[error("Contract call failed: {0}")]
    ContractCall(String),

    // =========================================================================
    // Generic Errors
    // =========================================================================
    /// Catch-all for unexpected errors
    #[error("Internal error: {0}")]
    Internal(String),
}

// =============================================================================
// Convert AppError to HTTP Response
// =============================================================================
//
// Axum needs to know how to convert our errors into HTTP responses.
// We implement the `IntoResponse` trait to do this.
//
// This is similar to Express error middleware that converts errors to JSON.

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        // Determine HTTP status code based on error type
        let status = match &self {
            // 404 Not Found - resource doesn't exist
            AppError::ChannelNotFound(_) => StatusCode::NOT_FOUND,

            // 400 Bad Request - client sent invalid data
            AppError::ChannelExpired
            | AppError::InsufficientBalance
            | AppError::InvalidSignature { .. }
            | AppError::MalformedSignature(_)
            | AppError::InvalidSequenceNumber { .. }
            | AppError::BalanceOverflow => StatusCode::BAD_REQUEST,

            // 500 Internal Server Error - something went wrong on our side
            AppError::Database(_) | AppError::ContractCall(_) | AppError::Internal(_) => {
                StatusCode::INTERNAL_SERVER_ERROR
            }
        };

        // Create JSON error response body
        // json!() is a macro that creates serde_json::Value
        let body = Json(json!({
            "error": self.to_string()
        }));

        // Combine status code and body into a Response
        // (status, body).into_response() is a tuple that implements IntoResponse
        (status, body).into_response()
    }
}
