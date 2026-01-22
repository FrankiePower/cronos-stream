# CronosStream Architecture

> Payment Channels for High-Frequency x402 Micropayments on Cronos

## The Problem

Standard x402 requires one on-chain transaction per payment:

```
Agent A                                      Agent B's API
   │                                              │
   │  API call #1                                 │
   ├─────────────────────────────────────────────>│
   │  "Pay me $0.01 first"                        │
   │<─────────────────────────────────────────────┤
   │                                              │
   │  On-chain tx #1 ($0.01)  [~3 sec wait]       │
   ├─────────────────────────────────────────────>│
   │  Here's your data                            │
   │<─────────────────────────────────────────────┤
   │                                              │
   │  API call #2                                 │
   ├─────────────────────────────────────────────>│
   │  On-chain tx #2 ($0.01)  [~3 sec wait]       │
   ├─────────────────────────────────────────────>│
   │  Here's your data                            │
   │<─────────────────────────────────────────────┤
   │                                              │
   │  ... repeat 998 more times ...               │

Total: 1000 on-chain transactions
Time:  1000 × 5 sec = 83 minutes just waiting for blockchain
```

**This doesn't work for agent-to-agent economies.**

---

## The Solution

CronosStream batches 1000 payments into 2 on-chain transactions:

```
Agent A                                      Agent B's API
   │                                              │
   │  ══════════════════════════════════════════  │
   │  ONCE: Open channel, deposit $10             │
   │  ══════════════════════════════════════════  │
   │                                              │
   │  On-chain tx #1: Lock $10 in contract        │
   ├─────────────────────────────────────────────>│
   │                                              │
   │  ══════════════════════════════════════════  │
   │  1000x: Just signatures, no blockchain       │
   │  ══════════════════════════════════════════  │
   │                                              │
   │  API call #1 + signed voucher "I owe $0.01"  │
   ├─────────────────────────────────────────────>│
   │  Here's your data (instant)                  │
   │<─────────────────────────────────────────────┤
   │                                              │
   │  API call #2 + signed voucher "I owe $0.02"  │
   ├─────────────────────────────────────────────>│
   │  Here's your data (instant)                  │
   │<─────────────────────────────────────────────┤
   │                                              │
   │  ... repeat 998 more times (all instant) ... │
   │                                              │
   │  ══════════════════════════════════════════  │
   │  ONCE: Close channel, settle up              │
   │  ══════════════════════════════════════════  │
   │                                              │
   │  On-chain tx #2: Pay Agent B $10             │
   ├─────────────────────────────────────────────>│

Total: 2 on-chain transactions
Time:  Instant API responses
```

---

## How It Works

### The Contract

CronosStream contract holds funds in escrow:

```
┌─────────────────────────────────────────────────────────┐
│              CronosStream Contract                      │
│                                                         │
│  Agent A deposits $10                                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Channel:                                         │  │
│  │    Owner: Agent A                                 │  │
│  │    Recipient: Agent B                             │  │
│  │    Locked: $10 USDC                               │  │
│  │    Owed to B: $0 → $0.01 → $0.02 → ... → $10     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  On close: Contract sends owed amount to Agent B        │
│            Returns remainder to Agent A                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### The Vouchers

Each payment is just a signed message (no blockchain):

```json
{
  "channelId": "0xabc123...",
  "amount": "2000000",
  "sequenceNumber": 42,
  "signature": "0xdef456..."
}
```

Agent B verifies the signature and delivers the service. No waiting for blocks.

### The Sequencer

Off-chain service that:
- Tracks channel state
- Validates voucher signatures
- Co-signs state updates
- Can close channels on-chain when needed

---

## Using Cronos Facilitator

We use the existing Cronos Facilitator for on-chain transactions:

```
OPEN CHANNEL:
   Agent A  ──── $10 USDC ────>  CronosStream Contract
                    │
                    └── Cronos Facilitator submits tx (EIP-3009)


CLOSE CHANNEL:
   CronosStream Contract  ──── $10 USDC ────>  Agent B
                                   │
                                   └── Contract distributes funds
```

The Facilitator handles the USDC transfers. Our Sequencer handles the off-chain voucher validation.

---

## Component Summary

| Component | Role |
|-----------|------|
| **CronosStream Contract** | Holds USDC deposits, verifies signatures, distributes on close |
| **Sequencer** | Off-chain state tracking, voucher validation, co-signing |
| **Cronos Facilitator** | Submits on-chain USDC transactions (open channel) |
| **SDK** | Client-side voucher signing, channel management |

---

## Comparison

| Metric | Standard x402 | CronosStream |
|--------|--------------|--------------|
| On-chain txns for 1000 payments | 1000 | 2 |
| Time waiting for blockchain | ~83 minutes | ~10 seconds |
| Gas cost | 1000× | 2× |
| Payment latency | ~5 sec each | Instant |

---

## References

- [x402 Protocol](https://www.x402.org/)
- [Cronos Facilitator SDK](https://www.npmjs.com/package/@crypto.com/facilitator-client)
- [EIP-712: Typed Structured Data Hashing](https://eips.ethereum.org/EIPS/eip-712)
