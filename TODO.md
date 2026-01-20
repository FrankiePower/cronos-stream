# CronosStream Build Plan

## Overview

Building CronosStream by adapting components from two reference projects:
- **Reference-1**: `reference-1/x402-hackathon/` - Cheddr payment channels (contracts, sequencer, demo client)
- **Reference-2**: `reference-2/x402-examples/` - Standard x402 (facilitator integration, resource service)

---

## 1. Smart Contracts

**Reference**: `reference-1/x402-hackathon/contracts/hardhat/`

| Task | Status |
|------|--------|
| Copy X402CheddrPaymentChannel.sol → CronosStream.sol | ⬜ |
| Copy TestUSDC.sol for local testing | ⬜ |
| Set up Hardhat config for Cronos testnet | ⬜ |
| Copy and run contract tests | ⬜ |
| Deploy contracts to Cronos testnet | ⬜ |

**Key Files**:
- `reference-1/x402-hackathon/contracts/hardhat/contracts/X402CheddrPaymentChannel.sol`
- `reference-1/x402-hackathon/contracts/hardhat/contracts/TestUSDC.sol`
- `reference-1/x402-hackathon/contracts/hardhat/hardhat.config.ts`

---

## 2. Sequencer Service

**Reference**: `reference-1/x402-hackathon/apps/sequencer/` (Rust)

| Task | Status |
|------|--------|
| Decide: Port to TypeScript or keep Rust | ⬜ |
| Implement channel state management | ⬜ |
| Implement voucher validation + co-signing | ⬜ |
| Implement channel close/finalize endpoints | ⬜ |
| Set up database (Postgres) | ⬜ |

**Key Files**:
- `reference-1/x402-hackathon/apps/sequencer/src/service.rs` - Core logic
- `reference-1/x402-hackathon/apps/sequencer/src/model.rs` - Data models
- `reference-1/x402-hackathon/apps/sequencer/src/crypto.rs` - Signature handling
- `reference-1/x402-hackathon/apps/sequencer/src/handlers.rs` - API endpoints

---

## 3. TypeScript SDK

**Reference**: `reference-1/x402-hackathon/apps/demo-client/`

| Task | Status |
|------|--------|
| Channel management (open/close) | ⬜ |
| EIP-712 voucher signing | ⬜ |
| Voucher verification helpers | ⬜ |
| x402 middleware integration | ⬜ |
| Publish as @cronos-stream/sdk | ⬜ |

**Key Files**:
- `reference-1/x402-hackathon/apps/demo-client/index.ts` - Full client implementation
- `reference-1/x402-hackathon/docs/x402-eip155-cpc-schema.md` - Schema spec

---

## 4. Resource Service (Demo API)

**Reference**: `reference-2/x402-examples/a2a/resource-service/`

| Task | Status |
|------|--------|
| Copy Express service structure | ⬜ |
| Add 'stream' scheme to 402 response | ⬜ |
| Integrate with Sequencer for validation | ⬜ |
| Integrate with Cronos Facilitator for channel open | ⬜ |

**Key Files**:
- `reference-2/x402-examples/a2a/resource-service/src/lib/middlewares/require.middleware.ts`
- `reference-2/x402-examples/a2a/resource-service/src/services/resource.service.ts`
- `reference-2/x402-examples/a2a/resource-service/src/services/resource.interface.ts`

---

## 5. Demo Client

**Reference**: `reference-1/x402-hackathon/apps/demo-client/`

| Task | Status |
|------|--------|
| Agent A: Opens channel, makes 100+ API calls | ⬜ |
| Agent B: Validates vouchers, delivers service | ⬜ |
| Dashboard showing live payment counter | ⬜ |
| Benchmark: payments per second | ⬜ |

**Key Files**:
- `reference-1/x402-hackathon/apps/demo-client/index.ts`
- `reference-1/x402-hackathon/apps/demo-client/benchmark.ts`

---

## 6. Documentation + Submission

| Task | Status |
|------|--------|
| Update README with setup instructions | ⬜ |
| Create x402 integration guide | ⬜ |
| Record 3.5 min demo video | ⬜ |
| Deploy to Cronos testnet | ⬜ |
| Submit to DoraHacks | ⬜ |

---

## File Structure (Target)

```
cronos-stream/
├── contracts/
│   ├── src/
│   │   ├── CronosStream.sol
│   │   └── interfaces/
│   ├── test/
│   └── hardhat.config.ts
├── sequencer/
│   ├── src/
│   └── package.json
├── sdk/
│   ├── src/
│   └── package.json
├── demo/
│   ├── service/          (Agent B - paywall API)
│   ├── client/           (Agent A - payer)
│   └── dashboard/
├── docs/
├── ARCHITECTURE.md
├── TODO.md
└── README.md
```

---

## Current Focus

**Step 1: Smart Contracts** ← START HERE
