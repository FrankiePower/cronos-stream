# CronosStream

**High-Frequency Layer 2 Streaming Payments for AI Agents on Cronos.**

CronosStream is a payment infrastructure enabling AI Agents to perform high-frequency, low-latency micro-transactions using EIP-712 off-chain vouchers and on-chain settlement.

## 🚀 Status: Production Ready (v1.0.0)
*   **Network**: Cronos Testnet (Chain ID 338).
*   **Performance**: ~150ms latency, >3 tx/sec verified.
*   **Security**: Fully non-custodial with on-chain settlement.

## 📂 Project Structure
*   `a2a/`: AI Agent and Resource Service implementation.
*   `sequencer/`: Rust-based high-performance validator/sequencer.
*   `contracts/`: Solidity smart contracts (StreamChannel).
*   `demo/`: Docker orchestration for universal deployment.
*   `scripts/`: Utility scripts for verification and management.

## ⚡ Quick Start

### 1. Requirements
*   Docker & Docker Compose.
*   Python 3.11+.
*   Rust (Wait, Sequencer runs in Docker, so optional).
*   Node.js (for Resource Service).

### 2. Launch Services
```bash
cd demo
./start.sh
```

### 3. Run the Agent
```bash
cd a2a/a2a-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m host.main
```

## 🛠️ Verification & Scripts
Located in `scripts/`:
*   `check_balance.py`: Verify Agent's USDC/TCRO balance.
*   `verify_settlement.py`: Trigger strict on-chain settlement.
*   `open_channel.py`: Manually open a channel (if not using the Agent's auto-logic).

## 📚 Documentation
*   [Release Notes](RELEASE_NOTES.md): Version history and feature summary.
*   `walkthrough.md`: Detailed step-by-step guide of the integration (in data artifacts).
*   `ARCHITECTURE.md`: High-level system design.

## 🔗 Contract Addresses (Testnet)
*   **StreamChannel**: `0xE118E04431853e9df5390E1AACF36dEF6A7a0254`
*   **devUSDC**: `0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0`
