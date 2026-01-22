# ⚡ CronosStream

### **The High-Throughput Settlement Layer for Agentic Commerce.**

**Scaling AI-to-AI micro-transactions on Cronos via verifiable off-chain state channels.**

## 🔗 Contract Addresses (Cronos Testnet)
*   **StreamChannel**: [`0xE118E04431853e9df5390E1AACF36dEF6A7a0254`](https://explorer.cronos.org/testnet/address/0xE118E04431853e9df5390E1AACF36dEF6A7a0254)

*   **devUSDC**: [`0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0`](https://explorer.cronos.org/testnet/address/0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0)

## 🚀 Status: Production Ready (v1.0.0)
*   **Network**: Cronos Testnet (Chain ID 338).
*   **Performance**: ~150ms latency, >14 tx/sec verified.
*   **Security**: Non-custodial, trust-minimized, strictly verifiable on-chain settlement.

## 🎭 The Scenario: Scaling the "Inference Economy"

In a multi-agent workflow, an **Aggregator Agent** might need to query 50 **Sub-Agents** for real-time data or compute.

*   **The Constraint**: Standard L1/L2 transactions, while secure, introduce a "Confirmation Tax." Even a 5-second block time creates a bottleneck for an AI that processes 100 tokens per second. Furthermore, 1,000 micro-payments for 0.001 USDC each would be economically non-viable due to cumulative gas costs.
*   **The Execution**: With **CronosStream**, the Aggregator opens a unidirectional payment channel on the Cronos Mainnet.
*   **The Stream**: As the Sub-Agents deliver data, the Aggregator issues **EIP-712 signed vouchers**. These are off-chain state updates that represent a cryptographically guaranteed claim on the locked collateral.
*   **The Result**: The Sub-Agent receives "payment" in ~70ms. The transaction remains off-chain until the session concludes, at which point a single **Atomic Settlement** transaction is pushed to Cronos.

---

## 🛠️ Technical Breakdown: How it Works

CronosStream moves the "transaction burden" away from the EVM's consensus layer and into a high-performance signing layer.

### 1. The Commitment (On-Chain)
The sender deposits funds into the `StreamChannel` smart contract. This creates a non-custodial escrow that defines the **Sender**, the **Recipient**, and the **Expiration**.

### 2. The Streaming (Off-Chain)
Payments are exchanged as **EIP-712 Typed Data**.

*   **Why EIP-712?** It provides a structured, human-and-machine-readable format for the transaction that ensures the signature cannot be replayed on other contracts or chains.
*   **The Latency**: Since this is a direct peer-to-peer exchange of signatures, throughput is limited only by network I/O and signing speed (benchmarked at ~14 TPS per agent).

### 3. Strictly Verifiable Settlement (On-Chain)
The recipient can withdraw their balance at any time by submitting the **latest voucher**.

*   **The Logic**: The contract recovers the signer's address from the EIP-712 signature. If the signature is valid and the amount is higher than the last withdrawn amount, the funds are released.

### 🏗️ Architecture Flow

```mermaid
flowchart TB
    subgraph OnChain ["⛓️ On-Chain (Cronos Mainnet)"]
        direction TB
        Contract[StreamChannel Contract<br/>(Locked Collateral)]
    end

    subgraph OffChain ["🚀 Off-Chain Layer (P2P)"]
        direction LR
        Sender[Aggregator Agent]
        Recipient[Sub-Agent]
        Voucher["📄 EIP-712 Voucher<br/>(Signed Commitment)"]
    end

    Sender -- "1. Deposit USDC" --> Contract
    Sender -- "2. Stream Vouchers" --> Voucher
    Voucher -- "Micro-payment" --> Recipient
    Recipient -- "3. Atomic Settlement" --> Contract
    Contract -- "Withdraw Funds" --> Recipient

    style Contract fill:#ff9900,stroke:#333,stroke-width:2px
    style Voucher fill:#66bb6a,stroke:#333,stroke-width:2px
```




## 📊 Performance Benchmarks (The "Hard" Data)

| Feature | Cronos L1 Transaction | CronosStream (Voucher) |
| :--- | :--- | :--- |
| **Settlement Speed** | ~5.0s (Block Time) | **< 100ms** (Signature Exchange) |
| **Cost per Tx** | $0.01 - $0.10+ | **$0.00** (Zero Gas) |
| **Verification** | Global Consensus | **Cryptographic (EIP-712)** |
| **Scalability** | Limited by Block Space | **Limited by Agent Compute** |

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

### 2. Launch Everything (Unified Start)
In one terminal, run the start script. This boots Docker (Infrastructure) AND the AI Agent (Background Service).
```bash
cd demo
./start.sh
```

### 3. Interact (The Demo)
In a second terminal, run the interactive CLI. This opens a shell where you can chat with the agent, check balances, and see detailed execution traces (including payment vouchers and channel IDs).
```bash
cd demo
./agent.sh
# Then type: "I want to access the premium content"
```

### 6. Run Benchmarks
To run the performance suite (TPS, Latency):
```bash
./demo/benchmark.sh
```

### 7. Stop Everything
When finished, run the stop script to cleanly shut down Docker and the background Agent process.
```bash
cd demo
./stop.sh
```

### 4. Stopping Services
To stop the demo environment and clean up resources:
```bash
cd demo
docker compose down
# Kill any lingering Python agent processes
pkill -f "python3 -m host.main"
```

## � Documentation
We have organized detailed documentation in the `docs/` folder:

## 📂 Documentation for Technical Review

*   **[Technical Architecture](docs/ARCHITECTURE.md)**: Deep dive into the Rust-based sequencer and state management.
*   **[Benchmark Methodology](docs/BENCHMARK_REPORT.md)**: How we measured 14 TPS real-time signing.
*   **[Contract Security](docs/MIGRATION_GUIDE.md)**: Analysis of the non-custodial escrow logic.
*   **[Walkthrough](docs/walkthrough.md)**: Detailed step-by-step integration guide.
*   **[Code Tour](docs/CODE_TOUR.md)**: Annotated guide to key source files.

## 📂 Project Structure
*   `a2a/`: AI Agent and Resource Service (Python).
*   `sequencer/`: High-performance Validator/Sequencer (Rust).
*   `contracts/`: Solidity smart contracts (StreamChannel).
*   `demo/`: Docker orchestration and startup scripts.
*   `scripts/`: Utility scripts for verification and management.

