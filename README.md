# CronosStream

**High-Frequency Layer 2 Streaming Payments for AI Agents on Cronos.**

> **Tagline**: "1000 payments. 2 transactions. Instant settlement."

CronosStream is a payment infrastructure enabling AI Agents to perform high-frequency, low-latency micro-transactions using EIP-712 off-chain vouchers and strictly verifiable on-chain settlement.

## 🚀 Status: Production Ready (v1.0.0)
*   **Network**: Cronos Testnet (Chain ID 338).
*   **Performance**: ~150ms latency, >14 tx/sec verified.
*   **Security**: Non-custodial, trust-minimized, strictly verifiable on-chain settlement.

## ⚡ The Problem & Solution
**The Bottleneck**: Traditional blockchain transactions are too slow (5s+) and expensive for AI-to-AI interaction (e.g., token-by-token streaming or high-frequency sensor data). A bot shouldn't wait for a block confirmation to pay 0.0001 USDC.

**The Solution**: **Payment Channels**.
1.  **Fund**: Agent A locks USDC in a smart contract.
2.  **Stream**: Agent A signs off-chain vouchers to Agent B (instant, free).
3.  **Settle**: Agent B submits the final voucher to validly withdraw funds.

## 📊 Proven Benchmarks
We rigorously benchmarked the system using a dedicated [Benchmark Suite](docs/BENCHMARK_REPORT.md).

| Metric | Off-Chain Demo | CronosStream (Verified) |
| :--- | :--- | :--- |
| **Throughput** | Theoretical Max | **27.81 TPS** (Burst Capacity) |
| **Live Signing** | N/A | **14.00 TPS** (Real-time Agent) |
| **Latency** | ~2.8s | **~0.07s** (70ms) |
| **Reliability** | Variable | **100% Success** (0 failures in 1000 reqs) |

## 💡 Use Cases

### 1. AI Agent Swarms
An Orchestrator Agent coordinates 5 specialist agents, exchanging 100 messages back-and-forth per task.
*   **Without CronosStream**: 500 transactions, high gas costs, slow.
*   **With CronosStream**: 2 transactions (Open/Close). Instant communication.

### 2. Token-Streaming Paywalls
Users pay per-token for LLM generation.
*   **Flow**: User signs a voucher for every 10 tokens generated.
*   **Benefit**: No risk of unpaid usage for the provider; no risk of overpayment for the user.

### 3. High-Frequency Data Feeds
Trading bots subscribing to sub-second price updates from an Oracle Agent.

## ⚡ Quick Start

### 1. Prerequisites
*   Docker & Docker Compose.
*   Python 3.11+.
*   Node.js (for Resource Service).

### 2. Launch Services (Universal Setup)
This script bootstraps the entire stack (Sequencer, Resource Service, DB):
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

## � Documentation
We have organized detailed documentation in the `docs/` folder:

*   **[Architecture](docs/ARCHITECTURE.md)**: High-level system design and component interaction.
*   **[Walkthrough](docs/walkthrough.md)**: Detailed step-by-step integration guide.
*   **[Benchmark Report](docs/BENCHMARK_REPORT.md)**: Full performance analysis and methodology.
*   **[Explainer Video Pitch](docs/VIDEO_PITCH.md)**: Script for the project video.
*   **[Migration Guide](docs/MIGRATION_GUIDE.md)**: Technical deep dive on the upgrade from reference implementation.
*   **[Code Tour](docs/CODE_TOUR.md)**: Annotated guide to key source files.
*   **[Release Notes](docs/RELEASE_NOTES.md)**: Version history (v1.0.0).

## 📂 Project Structure
*   `a2a/`: AI Agent and Resource Service (Python).
*   `sequencer/`: High-performance Validator/Sequencer (Rust).
*   `contracts/`: Solidity smart contracts (StreamChannel).
*   `demo/`: Docker orchestration and startup scripts.
*   `scripts/`: Utility scripts for verification and management.

## 🔗 Contract Addresses (Cronos Testnet)
*   **StreamChannel**: `0xE118E04431853e9df5390E1AACF36dEF6A7a0254`
*   **devUSDC**: `0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0`
