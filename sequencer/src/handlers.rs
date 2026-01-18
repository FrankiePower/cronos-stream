// handlers.rs - HTTP Route Handlers
//
// This file defines the HTTP API layer using axum.
// Handlers are thin - they just:
// 1. Extract request data
// 2. Call service functions
// 3. Return JSON responses

use axum::{
    extract::{Path, State},
    routing::{get, post},
    Json, Router,
};
use tracing::info;

use crate::{
    error::AppError,
    model::{
        ChannelView, ChannelsByOwnerResponse, FinalizeChannelRequest, FinalizeChannelResponse,
        PayInChannelRequest, PayInChannelResponse, SeedChannelRequest,
    },
    service,
    service::AppState,
};

// =============================================================================
// ROUTER SETUP
// =============================================================================

/// Create the HTTP router with all routes
///
/// This function is called from main.rs to set up the server.
/// `.with_state(state)` makes AppState available to all handlers.
pub fn create_router(state: AppState) -> Router {
    Router::new()
        // Health check endpoint (for load balancers, k8s probes, etc.)
        .route("/health", get(health))
        // List channels by owner (queries blockchain)
        .route("/channels/by-owner/:owner", get(list_channels_by_owner))
        // Register a new channel
        .route("/channel/seed", post(seed_channel))
        // Get channel state
        .route("/channel/:id", get(get_channel))
        // Close channel on-chain
        .route("/channel/finalize", post(finalize_channel))
        // Validate a voucher (read-only)
        .route("/validate", post(validate_pay_in_channel))
        // Process a voucher (updates state)
        .route("/settle", post(settle))
        // Attach the application state to all routes
        .with_state(state)
}

// =============================================================================
// HEALTH CHECK
// =============================================================================

/// Health check endpoint
///
/// Returns "ok" if the server is running.
/// Used by load balancers and container orchestrators.
///
/// `&'static str` = string literal with static lifetime (lives forever)
async fn health() -> &'static str {
    "ok"
}

// =============================================================================
// CHANNEL ENDPOINTS
// =============================================================================

/// List all channels owned by an address
///
/// GET /channels/by-owner/{owner}
///
/// `Path(owner)`: extracts `owner` from the URL path
/// `State(state)`: extracts AppState that was attached to router
async fn list_channels_by_owner(
    Path(owner): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<ChannelsByOwnerResponse>, AppError> {
    let response = service::list_channels_by_owner(&state, owner).await?;
    Ok(Json(response))
}

/// Register a newly opened channel
///
/// POST /channel/seed
/// Body: { channelId, owner, balance, expiryTimestamp }
///
/// `Json(payload)`: extracts and deserializes JSON body
async fn seed_channel(
    State(state): State<AppState>,
    Json(payload): Json<SeedChannelRequest>,
) -> Result<Json<ChannelView>, AppError> {
    // Log the request (structured logging)
    info!(
        channel_id = %payload.channel_id,
        owner = %payload.owner,
        balance = %payload.balance,
        expiry = payload.expiry_timestamp,
        "seed channel request"
    );

    let response = service::seed_channel(&state, payload).await?;
    Ok(Json(response))
}

/// Get channel state by ID
///
/// GET /channel/{id}
async fn get_channel(
    Path(channel_id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<ChannelView>, AppError> {
    let response = service::get_channel(&state, channel_id).await?;
    Ok(Json(response))
}

/// Validate a payment voucher (read-only)
///
/// POST /validate
/// Body: PayInChannelRequest
///
/// Checks if the voucher would be accepted without actually
/// processing it. Useful for UX (check before commit).
async fn validate_pay_in_channel(
    State(state): State<AppState>,
    Json(payload): Json<PayInChannelRequest>,
) -> Result<Json<PayInChannelResponse>, AppError> {
    info!(
        channel_id = %payload.channel_id,
        sequence_number = payload.sequence_number,
        "validate request"
    );

    let response = service::validate_pay_in_channel(&state, payload).await?;
    Ok(Json(response))
}

/// Finalize (close) a channel on-chain
///
/// POST /channel/finalize
/// Body: { channelId }
///
/// Calls the smart contract to distribute funds to recipients.
async fn finalize_channel(
    State(state): State<AppState>,
    Json(payload): Json<FinalizeChannelRequest>,
) -> Result<Json<FinalizeChannelResponse>, AppError> {
    info!(channel_id = %payload.channel_id, "finalize request");

    let response = service::finalize_channel(&state, payload).await?;
    Ok(Json(response))
}

/// Process a payment voucher (updates state)
///
/// POST /settle
/// Body: PayInChannelRequest
///
/// The main payment endpoint. Validates the voucher,
/// updates state, co-signs, and persists to database.
async fn settle(
    State(state): State<AppState>,
    Json(payload): Json<PayInChannelRequest>,
) -> Result<Json<PayInChannelResponse>, AppError> {
    info!(
        channel_id = %payload.channel_id,
        sequence_number = payload.sequence_number,
        "settle request"
    );

    let response = service::settle(&state, payload).await?;
    Ok(Json(response))
}

