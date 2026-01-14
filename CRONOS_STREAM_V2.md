# CronosStream

> **Payment Channels for High-Frequency x402 Micropayments on Cronos**

**Tagline**: "1000 payments. 2 transactions. Instant settlement."

---

## The Problem

x402 works great for one-off API payments. But agent-to-agent economies need high-frequency interactions:

| Use Case | Requests | x402 Today | Problem |
|----------|----------|------------|---------|
| Price feed agent | 100/min | 100 txns/min | $$$$ gas, network spam |
| AI agent conversation | 50 back-and-forth | 50 txns | Slow, expensive |
| Streaming data | Continuous | Infinite txns | Impossible |

**Cronos block time**: ~5-6 seconds
**Reality**: You can't build real-time agent economies waiting 5 seconds per payment.

---

## The Solution

CronosStream introduces **payment channels** to x402 - enabling thousands of instant micropayments settled in just 2 on-chain transactions.

```
WITHOUT CronosStream          WITH CronosStream
────────────────────          ─────────────────
Agent A ──tx1──> B            1. Open channel (1 tx)
Agent A ──tx2──> B               Deposit 10 USDC
Agent A ──tx3──> B
...                           2. Stream payments (off-chain)
Agent A ──tx1000──> B            Just signed messages
                                 Instant, free, unlimited
= 1000 transactions
= 1000 × gas                  3. Close channel (1 tx)
= 1000 × 5 sec wait              Settle final balance

                              = 2 transactions total
```

---

## How It Works

### Step 1: Open Channel
```solidity
// Agent A opens channel to Agent B
cronosStream.openChannel({
  recipient: agentB.address,
  deposit: 10_000000,  // 10 USDC (6 decimals)
  expiry: 24 hours
});
```
- Locks USDC in smart contract
- Creates channel: A → B
- Single on-chain transaction

### Step 2: Stream Payments (Off-Chain)
```typescript
// Agent A signs payment voucher
const voucher = await cronosStream.signPayment({
  channelId: "0x...",
  amount: 0.01,  // Cumulative amount owed
  nonce: 1
});

// Agent A sends voucher to Agent B (HTTP, WebSocket, etc.)
// Agent B verifies signature, delivers service
// NO blockchain interaction
```

Each payment is just a signed message:
```json
{
  "channelId": "0xabc123...",
  "amount": "10000",
  "nonce": 42,
  "signature": "0xdef456..."
}
```

### Step 3: Close Channel
```solidity
// Agent B closes with highest-nonce voucher
cronosStream.closeChannel({
  channelId: "0x...",
  amount: 9.50,  // Final amount owed
  nonce: 950,
  signature: "0x..."  // Agent A's signature
});
```
- Contract verifies signature
- Transfers owed amount to B
- Returns remainder to A
- Single on-chain transaction

### Step 4: Disputes (Safety Net)
```solidity
// If Agent B disappears, Agent A reclaims after timeout
cronosStream.timeoutChannel(channelId);

// If dispute, contract accepts highest valid nonce
cronosStream.dispute(channelId, amount, nonce, signature);
```

---

## x402 Integration

CronosStream extends x402 with a new `scheme: "stream"`:

### Standard x402 Response
```json
{
  "x402Version": 1,
  "accepts": [{
    "scheme": "exact",
    "network": "cronos",
    "asset": "0x...",
    "maxAmountRequired": "100000"
  }]
}
```

### CronosStream-Enhanced Response
```json
{
  "x402Version": 1,
  "accepts": [
    {
      "scheme": "exact",
      "network": "cronos",
      "asset": "0x...",
      "maxAmountRequired": "100000"
    },
    {
      "scheme": "stream",
      "network": "cronos",
      "asset": "0x...",
      "channelContract": "0x...",
      "recipient": "0x...",
      "pricePerRequest": "1000"
    }
  ]
}
```

**Client behavior**:
- Has open channel? → Use `stream` (instant)
- No channel? → Fall back to `exact` (standard x402)

---

## Smart Contract

### Interface
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface ICronosStream {
    struct Channel {
        address sender;
        address recipient;
        address token;
        uint256 deposit;
        uint256 expiry;
        bool closed;
    }

    // Open new payment channel
    function openChannel(
        address recipient,
        address token,
        uint256 amount,
        uint256 duration
    ) external returns (bytes32 channelId);

    // Close channel with final voucher
    function closeChannel(
        bytes32 channelId,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external;

    // Sender reclaims after timeout
    function timeoutChannel(bytes32 channelId) external;

    // Dispute with higher nonce voucher
    function dispute(
        bytes32 channelId,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external;

    // View functions
    function getChannel(bytes32 channelId) external view returns (Channel memory);
    function verifyVoucher(
        bytes32 channelId,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external view returns (bool);
}
```

### Channel ID
```solidity
channelId = keccak256(abi.encodePacked(
    sender,
    recipient,
    token,
    block.timestamp,
    nonce
));
```

### Voucher Signature (EIP-712)
```solidity
bytes32 voucherHash = keccak256(abi.encodePacked(
    "\x19\x01",
    DOMAIN_SEPARATOR,
    keccak256(abi.encode(
        VOUCHER_TYPEHASH,
        channelId,
        amount,
        nonce
    ))
));

address signer = ecrecover(voucherHash, v, r, s);
require(signer == channel.sender, "Invalid signature");
```

---

## TypeScript SDK

### Installation
```bash
npm install @cronos-stream/sdk
```

### Usage
```typescript
import { CronosStream } from '@cronos-stream/sdk';
import { ethers } from 'ethers';

// Initialize
const stream = new CronosStream({
  provider: new ethers.JsonRpcProvider('https://evm.cronos.org'),
  signer: wallet,
  contractAddress: '0x...'
});

// Open channel
const channelId = await stream.openChannel({
  recipient: '0xAgentB...',
  token: USDC_ADDRESS,
  amount: ethers.parseUnits('10', 6),  // 10 USDC
  duration: 24 * 60 * 60  // 24 hours
});

// Sign payment (off-chain)
const voucher = await stream.signPayment(channelId, {
  amount: ethers.parseUnits('0.01', 6),
  nonce: 1
});

// Send voucher to recipient (your transport)
await sendToAgentB(voucher);

// Recipient verifies (off-chain)
const isValid = await stream.verifyVoucher(voucher);

// Close channel (on-chain)
await stream.closeChannel(channelId, finalVoucher);
```

### x402 Middleware
```typescript
import { cronosStreamMiddleware } from '@cronos-stream/sdk';

// Add to x402 client
const x402Client = new X402Client({
  middlewares: [
    cronosStreamMiddleware({
      stream,
      autoOpenChannel: true,
      defaultDeposit: ethers.parseUnits('1', 6)
    })
  ]
});

// Now x402 requests auto-use channels when available
const response = await x402Client.fetch('https://agent-b.com/api/data');
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CronosStream                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Agent A (Payer)                    Agent B (Payee)            │
│   ┌─────────────┐                    ┌─────────────┐            │
│   │ CronosStream│                    │ CronosStream│            │
│   │    SDK      │                    │    SDK      │            │
│   └──────┬──────┘                    └──────┬──────┘            │
│          │                                  │                   │
│          │  1. openChannel (on-chain)       │                   │
│          ├─────────────────────────────────>│                   │
│          │                                  │                   │
│          │  2. signPayment ──voucher──>     │                   │
│          │     signPayment ──voucher──>     │  (off-chain,      │
│          │     signPayment ──voucher──>     │   instant,        │
│          │     ... (1000x) ...              │   free)           │
│          │                                  │                   │
│          │  3. closeChannel (on-chain)      │                   │
│          │<─────────────────────────────────┤                   │
│          │                                  │                   │
│   ┌──────┴──────────────────────────────────┴──────┐            │
│   │            CronosStream Contract               │            │
│   │  - Channel state (deposit, expiry, closed)     │            │
│   │  - EIP-712 signature verification              │            │
│   │  - Dispute resolution                          │            │
│   │  - Timeout handling                            │            │
│   └────────────────────────┬───────────────────────┘            │
│                            │                                    │
│                   ┌────────┴────────┐                           │
│                   │ Cronos Blockchain│                          │
│                   │   (USDC Token)   │                          │
│                   └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Cases

### 1. Real-Time Price Oracle
```
DeFi bot needs ETH/USD price every second
- Opens 10 USDC channel to Oracle Agent
- Queries price 3600x/hour (1/sec)
- Each query = 0.001 USDC voucher
- Settles once per hour
- Cost: 3.60 USDC + 2 tx gas
- Without channels: 3600 tx gas = $$$
```

### 2. AI Agent Swarm
```
Orchestrator coordinates 5 specialist agents
- Opens channel to each agent
- 100 messages back-and-forth per task
- Each message = micropayment
- Task complete → close channels
- Instant communication, no tx delays
```

### 3. Streaming Data Feed
```
Trading bot subscribes to market data
- Opens channel, starts receiving
- Pays per data point received
- Closes channel when done
- Pay-per-use, no subscriptions
```

### 4. High-Frequency Arbitrage
```
Arb bot queries 10 DEX agents
- Needs sub-second responses
- Opens channels to all DEXs
- Queries prices instantly (off-chain)
- Executes arb on best spread
- Settles channels daily
```

---

## Development Plan

### Phase A: Core (Week 1-2) ✅ CURRENT FOCUS
- [ ] Smart contract (Solidity)
  - [ ] Channel open/close
  - [ ] EIP-712 voucher verification
  - [ ] Timeout mechanism
  - [ ] Basic dispute handling
- [ ] TypeScript SDK
  - [ ] Channel management
  - [ ] Voucher signing/verification
  - [ ] x402 middleware
- [ ] Deploy to Cronos testnet

### Phase B: Gas Abstraction (Week 3) 🔮 IF TIME PERMITS
- [ ] Integrate gas abstraction (pay gas in USDC)
- [ ] Agents never need CRO
- [ ] Meta-transactions for channel operations

---

## Demo Script (3.5 minutes)

### 0:00 - 0:30 | The Problem
"x402 is great for one-off payments. But what happens when Agent A needs to call Agent B 1000 times per hour? 1000 transactions, 1000 gas fees, 5 second waits. Agent economies can't scale like this."

### 0:30 - 1:30 | The Solution
"CronosStream introduces payment channels to x402. Watch."
- Show Agent A opening channel (1 tx)
- Show 100 payments streaming in real-time (counter going up)
- Show Agent B closing channel (1 tx)
- "1000 payments. 2 transactions. Instant."

### 1:30 - 2:30 | Technical Deep Dive
- Show smart contract
- Show EIP-712 voucher structure
- Show x402 integration (`scheme: "stream"`)
- "Fully compatible with existing x402. Just a new scheme."

### 2:30 - 3:00 | Use Cases
- Price oracles
- AI agent swarms
- Streaming data
- "Any high-frequency agent interaction"

### 3:00 - 3:30 | Why Cronos
- "Cronos has the facilitator SDK, the ecosystem, and now - with CronosStream - the scalability layer for agent economies."
- Show gas savings calculator
- "This is infrastructure others can build on."

---

## File Structure

```
cronos-stream/
├── contracts/
│   ├── CronosStream.sol
│   ├── interfaces/
│   │   └── ICronosStream.sol
│   └── test/
│       └── CronosStream.test.ts
├── sdk/
│   ├── src/
│   │   ├── index.ts
│   │   ├── CronosStream.ts
│   │   ├── voucher.ts
│   │   └── middleware.ts
│   ├── package.json
│   └── tsconfig.json
├── demo/
│   ├── agent-a/
│   │   └── index.ts
│   ├── agent-b/
│   │   └── index.ts
│   └── dashboard/
│       └── (React app showing live payments)
├── docs/
│   └── x402-integration.md
└── README.md
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Channel open gas | < 100k gas |
| Channel close gas | < 80k gas |
| Voucher verification | < 1ms (off-chain) |
| Demo throughput | 100+ payments/sec |
| x402 compatibility | 100% backward compatible |

---

## References

- [Cheddr (Base implementation)](https://github.com/CPC-Development/x402-hackathon)
- [x402 Protocol](https://www.x402.org/)
- [Cronos Facilitator SDK](https://www.npmjs.com/package/@crypto.com/facilitator-client)
- [EIP-712: Typed Structured Data Hashing](https://eips.ethereum.org/EIPS/eip-712)
- [Payment Channels (Ethereum.org)](https://ethereum.org/en/developers/docs/scaling/state-channels/)

---

## Team

- **Builder**: [Your Name]
- **Track**: Dev Tooling & Data Virtualization Track
- **Hackathon**: Cronos x402 Paytech Hackathon (Dec 2025 - Jan 2026)
