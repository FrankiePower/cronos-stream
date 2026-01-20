# CronosStream

> **Payment Channels for High-Frequency Agent-to-Agent Micropayments on Cronos**

## The Problem

x402 is great for one-off API payments, but breaks down for high-frequency agent interactions:

| Scenario | x402 Today | Problem |
|----------|-----------|---------|
| Agent queries price feed 100x/min | 100 on-chain transactions | Gas costs explode |
| AI agent calls another agent 1000x/hour | 1000 tx, wait for finality each time | Too slow, too expensive |
| Streaming data feed (real-time) | Continuous transactions | Network spam, unsustainable |

**Cronos block time**: ~5-6 seconds
**Result**: High-frequency agent economies are impossible with transaction-per-request model.

---

## The Solution: Payment Channels

CronosStream introduces **payment channels** to x402 on Cronos - enabling thousands of micropayments with only 2 on-chain transactions.

```
┌─────────────────────────────────────────────────────────────────┐
│                     WITHOUT CronosStream                        │
├─────────────────────────────────────────────────────────────────┤
│  Agent A ──tx1──> Agent B                                       │
│  Agent A ──tx2──> Agent B                                       │
│  Agent A ──tx3──> Agent B                                       │
│  ...                                                            │
│  Agent A ──tx1000──> Agent B                                    │
│                                                                 │
│  = 1000 on-chain transactions                                   │
│  = 1000 × gas fees                                              │
│  = 1000 × wait for block confirmation                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      WITH CronosStream                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Agent A opens channel (1 on-chain tx, deposits 10 USDC)     │
│  2. Agent A ──signed msg──> Agent B  (off-chain)                │
│     Agent A ──signed msg──> Agent B  (off-chain)                │
│     Agent A ──signed msg──> Agent B  (off-chain)                │
│     ... 1000 payments ...                                       │
│  3. Agent B closes channel (1 on-chain tx, claims 10 USDC)      │
│                                                                 │
│  = 2 on-chain transactions                                      │
│  = 2 × gas fees                                                 │
│  = Instant off-chain payments                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Open Channel
```
Agent A deposits USDC into CronosStream smart contract
Channel created: A → B, 10 USDC capacity, 24hr expiry
```

### 2. Stream Payments (Off-Chain)
```
Each "payment" is a signed message:
{
  channelId: "0x...",
  amount: "0.01",        // cumulative amount owed
  nonce: 1,
  signature: "0x..."     // Agent A's signature
}

Agent B verifies signature, delivers service
No blockchain interaction needed
```

### 3. Close Channel
```
Agent B submits final signed message to contract
Contract verifies signature, transfers funds
Channel closed
```

### 4. Disputes (Safety)
```
If Agent B disappears: Agent A can close after timeout
If Agent A disputes: Contract checks highest valid nonce
Trustless settlement on-chain
```

---

## Integration with x402

CronosStream extends x402, not replaces it:

```
Standard x402 Response (402 Payment Required):
{
  "accepts": [{
    "scheme": "exact",
    "network": "cronos",
    "asset": "USDC",
    "maxAmountRequired": "100000"  // 0.10 USDC
  }]
}

CronosStream-Enhanced Response:
{
  "accepts": [
    {
      "scheme": "exact",           // Standard x402 (fallback)
      "network": "cronos",
      "asset": "USDC",
      "maxAmountRequired": "100000"
    },
    {
      "scheme": "stream",          // CronosStream (preferred)
      "network": "cronos",
      "asset": "USDC",
      "channelContract": "0x...",
      "recipient": "0x...",
      "pricePerRequest": "1000"    // 0.001 USDC per request
    }
  ]
}
```

Agents can choose:
- **No channel?** Fall back to standard x402 (one-off payment)
- **Have channel?** Use streaming payment (instant, cheap)

---

## Use Cases

### 1. Real-Time Price Feeds
```
DeFi Agent needs price updates every second
Opens channel with Oracle Agent
1000 price queries = 0.10 USDC total
Settles once per hour
```

### 2. AI Agent Conversations
```
Planning Agent orchestrates 5 specialist agents
Each agent interaction = micropayment
100 back-and-forth messages = 100 payments
All off-chain, settles when task complete
```

### 3. Streaming Data Services
```
Trading bot subscribes to market data
Pay-per-second while connected
Stop paying = stop receiving
No subscriptions, pure usage-based
```

### 4. High-Frequency Arbitrage
```
Arb bot queries multiple DEX agents
Needs sub-second response times
Payment channels enable instant payments
No waiting for block confirmation
```

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CronosStream                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐         ┌─────────────┐                       │
│  │   Agent A   │         │   Agent B   │                       │
│  │  (Payer)    │         │  (Payee)    │                       │
│  └──────┬──────┘         └──────┬──────┘                       │
│         │                       │                               │
│         │  1. Open Channel      │                               │
│         ├──────────────────────>│                               │
│         │     (on-chain)        │                               │
│         │                       │                               │
│         │  2. Signed Payments   │                               │
│         │<─────────────────────>│                               │
│         │    (off-chain)        │                               │
│         │                       │                               │
│         │  3. Close Channel     │                               │
│         │<──────────────────────┤                               │
│         │     (on-chain)        │                               │
│         │                       │                               │
│  ┌──────┴──────────────────────┴──────┐                        │
│  │      CronosStream Smart Contract    │                        │
│  │  - Channel state management         │                        │
│  │  - Signature verification           │                        │
│  │  - Dispute resolution               │                        │
│  │  - Timeout handling                 │                        │
│  └─────────────────────────────────────┘                        │
│                       │                                         │
│                       │                                         │
│  ┌────────────────────┴────────────────┐                       │
│  │           Cronos Blockchain          │                       │
│  │         (USDC Settlement)            │                       │
│  └──────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components to Build

### 1. Smart Contract (Solidity)
- `openChannel(recipient, amount, expiry)`
- `closeChannel(channelId, amount, nonce, signature)`
- `disputeChannel(channelId, amount, nonce, signature)`
- `timeoutChannel(channelId)` - reclaim after expiry

### 2. SDK (TypeScript)
- `CronosStream.openChannel(recipient, deposit)`
- `CronosStream.signPayment(channelId, amount)`
- `CronosStream.verifyPayment(signedPayment)`
- `CronosStream.closeChannel(channelId, finalPayment)`

### 3. x402 Middleware
- Detect `scheme: "stream"` in payment requirements
- Auto-manage channels (open, pay, close)
- Fallback to standard x402 when no channel

### 4. Demo Application
- Two agents communicating via payment channel
- Visual dashboard showing off-chain payments
- Gas savings calculator

---

## Comparison with Cheddr (Base)

| Feature | Cheddr (Base) | CronosStream (Cronos) |
|---------|---------------|----------------------|
| Network | Base/Ethereum | Cronos |
| Facilitator | Custom | @crypto.com/facilitator-client |
| x402 Integration | Yes | Yes |
| Payment Channels | Yes | Yes |
| Dispute Resolution | ? | Yes |
| SDK | ? | TypeScript + Python |

---

## Development Roadmap

### Week 1: Smart Contract
- [ ] Payment channel contract
- [ ] Test on Cronos testnet
- [ ] Security review

### Week 2: SDK + Integration
- [ ] TypeScript SDK
- [ ] x402 middleware integration
- [ ] Python SDK for agents

### Week 3: Demo + Polish
- [ ] Demo application (2 agents)
- [ ] Documentation
- [ ] Video walkthrough

---

## Why This Wins

1. **Infrastructure** - Judges love infra (see Base hackathon winners)
2. **Real Problem** - High-frequency payments don't work today
3. **Enables Others** - Other devs can build on CronosStream
4. **Cronos-Native** - First payment channel solution for Cronos
5. **x402 Compatible** - Extends the protocol, doesn't replace it

---

## Resources

- [Cheddr (Base implementation)](https://github.com/CPC-Development/x402-hackathon)
- [x402 Protocol Spec](https://www.x402.org/)
- [Cronos Facilitator SDK](https://www.npmjs.com/package/@crypto.com/facilitator-client)
- [Payment Channels Explained](https://ethereum.org/en/developers/docs/scaling/state-channels/)

---

## Open Questions

- [ ] What's the optimal channel timeout duration?
- [ ] How to handle partial channel closures?
- [ ] Should channels be unidirectional or bidirectional?
- [ ] How to integrate with existing agent discovery (A2A)?
