# CronosStream v1.0.0 - Release Notes

## 🚀 Overview
CronosStream is a High-Frequency Layer 2 Streaming Payment solution for AI Agents on Cronos.
This release (`v1.0.0`) delivers a fully functional, production-ready implementation compliant with EIP-712 and EIP-3009, deployed on Cronos Testnet.

## ✨ Key Features
*   **On-Chain Hybrid Mode**:
    *   **Strict Mode**: Enforces real on-chain channel creation (`openChannel`) and funding with `devUSDC`.
    *   **Auto-Approval**: Automatically handles ERC20 `approve` transactions.
    *   **Optimistic Sync**: Seeds the off-chain sequencer only after on-chain transaction confirmation.
*   **Performance**:
    *   **Throughput**: 3.12 payments/sec (Benchmark verified).
    *   **Latency**: ~150ms per payment (Off-chain signage).
*   **Verification**:
    *   **End-to-End**: Verified flow from Agent -> Channel -> Sequencer -> Merchant.
    *   **Settlement**: Confirmed on-chain settlement with value transfer to Merchant address.

## 🛠️ Components
*   **Agent (`a2a-service`)**: Python-based AI Agent capable of discovering generic paywalls and negotiating streaming payments.
*   **Sequencer**: Rust-based high-performance validator ensuring double-spend protection and channel state management.
*   **Resource Service**: Typescript-based example service implementing the 402 Payment Required protocol.

## 📦 Verified Configuration
*   **Network**: Cronos Testnet (Chain ID 338)
*   **Channel Contract**: `0xE118E04431853e9df5390E1AACF36dEF6A7a0254`
*   **Token**: `devUSDC` (`0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0`)

## 📝 Usage
See `scripts/README.md` (or project root `README.md`) for setup instructions.
Key scripts:
*   `demo/start.sh`: Universal Docker setup.
*   `scripts/check_balance.py`: Check wallet funds.
*   `scripts/verify_settlement.py`: Trigger on-chain settlement.
