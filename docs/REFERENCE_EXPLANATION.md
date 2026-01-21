# Reference Implementation Analysis (`reference-1`)

This document details the architecture, testing strategy, and benchmarking methodology used in the reference project (`x402-hackathon`).

## 1. Demo Architecture & Orchestration
The demo is orchestrated via `scripts/run-demo.sh`, which performs a reproducible infrastructure bootstrapping:

1.  **Bootstrap (`infra/bootstrap-hardhat.sh`)**:
    *   Starts a local Hardhat node.
    *   Deploys the `StreamChannel` and `MockUSDC` contracts.
    *   Extracts the deployed addresses to `.env` files for other services to consume.
2.  **Containerization (`docker-compose.yml`)**:
    *   Runs the entire stack: Hardhat, Sequencer (Rust), Facilitator, Resource Service, and a Nominatim (Geo) service.
    *   This ensures "Production-like" topology.
3.  **Health-Checking**:
    *   The script actively polls the Resource Service (`/health`) to ensure readiness before launching clients.

## 2. Testing Methodology
The project treats the `apps/demo-client` as an **End-to-End Integration Test**.
Instead of just unit tests, the client (`index.ts`) executes a full user journey:
1.  **Discovery**: Requests `OPTIONS /requirements` (or similar) to find contract/token addresses.
2.  **Channel Lifecycle**:
    *   Checks for existing channels on the Sequencer.
    *   Checks on-chain contract state.
    *   **Self-Healing**: If no channel exists or balance is low, it automatically funds and opens a channel on-chain (Robust Logic).
3.  **Settlement**:
    *   Signs and sends payment.
    *   Retries the resource access to confirm `paid=True`.

## 3. Benchmark Methodology (`benchmark.ts`)
The benchmark script specifically isolates **Signing Latency** vs **Network Throughput**.

### A. Live Signing (End-to-End)
*   **Method**: A `while` loop runs for `BENCHMARK_SECONDS` (10s).
*   **Action**: `Sign` -> `Network Request` -> `Verify Response` -> `Repeat`.
*   **Metric**: Measures the real-world performance of an Agent doing work sequentially.
*   **Bottleneck**: CPU (Signing) + Network RTT.

### B. Pre-Signing (Maximizing Throughput)
*   **Method**:
    1.  Generates 10,000 (`PRESIGN_COUNT`) signatures in-memory and stores them in an array.
    2.  Fires them all to the server in a tight loop.
*   **Action**: `Network Request` -> `Network Request` ...
*   **Metric**: Measures the raw capacity of the **Sequencer** and **Service** to handle validated requests.
*   **Bottleneck**: Server-side validation logic and DB writes.

### C. Replication in CronosStream
We successfully replicated this methodology in `scripts/benchmark_suite.py`:
*   Implemented both "Live Signing" (sync) and "Pre-Signed" (burst) modes.
*   Verified against the Rust Sequencer with 100% success rate.
*   Achieved consistent metrics (14 TPS Live / 27.8 TPS Pre-Signed), validating the performance claims.

## 4. Key Takeaways for Our Implementation
*   **Hybrid On-Chain Logic**: We successfully adopted their "Test On-Chain, Fallback to Open" logic in our `ChannelManager`.
*   **Separation of Concerns**: They separate "Demo Logic" (one-off) from "Benchmark Logic" (performance stress test).
*   **Universal Config**: Their use of `infra/` to produce shared `.env` files for all services is a pattern we mimicked with our `demo/start.sh`.
