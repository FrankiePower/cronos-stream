# Polish & Finalize Checklist

This document tracks improvements and "technical debt" cleanups required to move the integration from a working demo to a production-ready system.

## High Priority
- [x] **Channel Persistence**: currently `service.py` generates a random channel ID on every restart (to avoid expiration issues). This means any funds deposited into that channel are "lost" (orphaned) when the agent restarts. We need to persist the `channel_id` (e.g., in a local JSON file or DB) so the agent can reuse the same funded channel across restarts.
- [x] **Dynamic Configuration**: `channel_manager.py` currently uses hardcoded values for `CONTRACT_ADDRESS` (0xe7f...) and `CHAIN_ID` (31337). These should be moved to the `.env` file so the agent can easily switch between Localhost, Testnet, and Mainnet without code changes.
- [x] **Sequencer Configuration**: `resource-service` relies on a default `localhost:3000` for the Sequencer URL. We should add `SEQUENCER_URL` to its `.env` and `.env.example` to make this explicit and configurable.
