# CronosStream Integration Deep Dive
*Technical Migration Report*

This document provides a line-by-line analysis of the changes required to upgrade the `reference-2` codebase to the full **CronosStream** architecture.

---

## 1. The Agent: `host/service.py`
**Goal**: Upgrade the agent from "One-Time Payments" (EIP-3009) to "Streaming Payments" (EIP-712).

### The Change: Intelligent Payment Selection
We modified `fetch_resource` to prioritize the `streaming` scheme over the standard `exact` scheme.

**Reference Implementation (Before):**
*Blindly takes the first payment option.*
```python
# reference-2/x402-examples/a2a/a2a-service/host/service.py:262
challenge = res.json()
accepts0 = (challenge.get("accepts") or [None])[0]  # <--- Just takes the first one
if not accepts0:
    raise ValidationError(...)

# Proceed to standard EIP-3009 payment...
payment_header = await self.generate_payment_header(accepts0)
```

**CronosStream Integration (After):**
*Checks for streaming capability and branches logic.*
```python
# a2a/a2a-service/host/service.py:261
challenge = res.json()
accepts_list = challenge.get("accepts") or []

# [NEW] Look for 'streaming' scheme specifically
streaming_opt = next((a for a in accepts_list if a.get("scheme") == "streaming"), None)
accepts0 = next((a for a in accepts_list if a.get("scheme") == "exact"), None)

# [NEW] Branch to streaming handler if available
if streaming_opt:
    return await self.handle_streaming_payment(client, resource_url, base, streaming_opt)

# Fallback to standard flow...
if not accepts0:
    accepts0 = accepts_list[0] if accepts_list else None
```

### The New Logic: `handle_streaming_payment`
We added this entire method to handle off-chain vouchers.

**Key Lines Added:**
```python
# a2a/a2a-service/host/service.py:321
async def handle_streaming_payment(self, ...):
    from .channel_manager import ChannelManager
    
    # 1. Initialize Channel Manager with random ID (Fix for expiration)
    import secrets
    channel_id = "0x" + secrets.token_hex(32)
    cm = ChannelManager(pk, channel_id, owner_acct.address)
    
    # 2. Ensure Channel exists on Sequencer
    await cm.ensure_channel(sequencer_url, ...)
    
    # 3. Create Off-Chain Voucher (No Gas!)
    voucher = cm.create_voucher(pay_to, amount)
    
    # 4. Settle via special endpoint
    pay_endpoint = f"{base_url}/api/pay-voucher"
    res = await client.post(pay_endpoint, json=voucher)
```

---

## 2. The Resource Service: `src/controllers/resource.controller.ts`
**Goal**: Enable the backend to accept off-chain vouchers and validate them with the Sequencer.

### The Change: New Endpoint
We added a dedicated handler for streaming vouchers completely separate from the standard `pay` endpoint.

**Reference Implementation (Before):**
*Only handles standard payments.*
```typescript
// reference-2/.../resource.controller.ts:58
public async pay(req: Request, res: Response, next: NextFunction) {
  // Accepts 'paymentHeader' (EIP-3009)
  // Validates locally or via standard library
}
```

**CronosStream Integration (After):**
*Refuses to blindly trust; delegates to Sequencer.*
```typescript
// a2a/resource-service/src/controllers/resource.controller.ts:102 [NEW]
public async payVoucher(req: Request, res: Response, next: NextFunction) {
  const { channelId, sequenceNumber, userSignature, ... } = req.body;

  // Delegate to service layer which calls Sequencer
  const response = await this.resourceService.settleVoucher({
    channelId,
    sequenceNumber,
    userSignature,
    // ...
  });
  
  return res.json(response);
}
```

### The New Client: `src/lib/sequencer.client.ts`
We introduced a dedicated client to talk to the Sequencer service. This decoupling ensures the backend logic remains clean.

**Key Logic:**
*   **`validateVoucher`**: Used for lightweight checks.
*   **`settleVoucher`**: Performs the state transition. This is the critical call that "finalizes" the payment off-chain.

```typescript
// src/lib/sequencer.client.ts
const SEQUENCER_URL = process.env.SEQUENCER_URL ?? 'http://localhost:3000';

export async function settleVoucher(voucher: VoucherPayload) {
  const response = await fetch(`${SEQUENCER_URL}/settle`, { ... });
  // ...
  return { ok: true, data };
}
```
**Configuration Note**: We default to `localhost:3000` but rely on `process.env.SEQUENCER_URL` for production deployment.

---

## 3. The Sequencer: `src/crypto.rs`
**Goal**: Align off-chain signature verification with the on-chain solidity contract.

### The Fix: Domain Name Matching
This was the critical bug fix. The off-chain signer (Python) and the on-chain contract (Solidity) must use the exact same "Domain Name" for EIP-712 hashing, otherwise verification fails.

**The Bug (Before):**
```rust
// sequencer/src/crypto.rs
const DOMAIN_NAME: &str = "CronosStream"; // <--- Mismatch!
```

**The Fix (After):**
```rust
// sequencer/src/crypto.rs
const DOMAIN_NAME: &str = "StreamChannel"; // <--- Matches StreamChannel.sol
```
*Why this matters: This string is hashed into every signature. A single character difference makes every payment fail.*

---

## 4. The New SDK: `host/channel_manager.py`
**Goal**: Encapsulate all EIP-712 state management and signing logic.

This is a **completely new file** we introduced. In the reference implementation, this logic did not exist.

**What it does:**
1.  **State Tracking**: Keeps track of `sequenceNumber` and `cumulative_amounts` (how much you've paid each recipient).
2.  **Seeding**: Talks to the Sequencer `POST /channel/seed` to register the channel off-chain.
3.  **Signing**: Uses `eth_account.messages.encode_typed_data` to generate the EIP-712 signature required by the smart contract.

**Key Code Snippet (EIP-712 Construction):**
```python
# channel_manager.py:82
data = {
    "types": { "EIP712Domain": [...], "ChannelData": [...] },
    "domain": {
        "name": "StreamChannel", # <--- Must match Contract!
        "version": "1",
        "chainId": self.chain_id,
        "verifyingContract": self.contract_address
    },
    "message": { ... }
}
encoded_msg = encode_typed_data(full_message=data)
```

**Hardcoding Note**: Currently, `CONTRACT_ADDRESS` and `CHAIN_ID` are hardcoded for the local Hardhat demo environment. In production, these should be loaded from environment variables.

---

## 5. Summary of Impact

| Component | Reference-2 Logic | CronosStream Logic | Impact |
| :--- | :--- | :--- | :--- |
| **Agent** | "Pay per request" (Tx) | "Sign per request" (Sig) | **Zero Latency** |
| **Backend** | Local Check | Remote Sequencer Check | **Scalable Validation** |
| **Security** | EIP-3009 (Token Transfer) | EIP-712 (Typed Data) | **Gasless & Secure** |
