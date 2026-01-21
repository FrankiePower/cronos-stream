# CronosStream Codebase Tour

This document verifies that our implementation matches the CronosStream architecture by breaking down the key files in the `a2a` directory.

## 1. The Agent (`a2a/a2a-service`)
*The "Spender" - Needs to buy resources fast.*

### `host/channel_manager.py` (The Wallet)
**Role**: Managing Off-Chain State.
This corresponds to the **"SDK"** in the architecture.
- **Key Logic**:
    - Holds the `X402_PRIVATE_KEY` for signing.
    - Tracks `sequenceNumber` (nonce) to prevent replay attacks.
    - **`create_voucher()`**: The core function. It takes a recipient and amount, increments the nonce, and generates an **EIP-712 Signature** ("I owe you X"). This signature is what acts as the "money" in the streaming layer.
    - **`ensure_channel()`**: Checks with the Sequencer if a channel exists; if not, it requests to "seed" one (register it).

### `host/service.py` (The Spender Logic)
**Role**: Business Logic & Payment Flow.
- **Key Logic**:
    - **`handle_streaming_payment()`**: This is the specialized function we added.
    - Instead of doing a blockchain transaction (which `eth_account` would usually do), it:
        1. Calls `ChannelManager` to get a signed voucher (instant).
        2. Sends this voucher via HTTP POST to the resource service (`/api/pay-voucher`).
        3. If successful, it gets the data.
    - This corresponds to the **"API call #1 + signed voucher"** arrow in the architecture diagram.

### `host/main.py`
**Role**: Entry Point.
- Sets up the `ChannelManager`.
- Starts the HTTP server (port 9001) so other agents can find *this* agent (if it were selling something), though in our test it acts primarily as a client.

---

## 2. The Resource Service (`a2a/resource-service`)
*The "Seller" - Validates payments and releases data.*

### `src/controllers/resource.controller.ts`
**Role**: The Gateway.
- **Key Logic**:
    - **`payVoucher` Endpoint**: Receives the EIP-712 voucher from the Agent.
    - It does **not** trust the Agent blindly. It forwards the voucher to the **Sequencer** to check if it's valid.
    - If the Sequencer says "Valid", it returns `{ ok: true }`.

### `src/services/resource.service.ts`
**Role**: Sequencer Client.
- **Key Logic**:
    - **`settleVoucher()`**: This function talks to the Sequencer (`http://localhost:3000/settle`).
    - It passes the voucher to the Sequencer. The Sequencer effectively acts as the "Bank" or "Validator" here, ensuring the Agent actually has the funds locked in the contract to back up this voucher.

### `src/lib/middlewares/require.middleware.ts`
**Role**: The Paywall (402).
- **Key Logic**:
    - When the Agent asks for data `GET /resource`, this middleware checks for payment.
    - If unpaid, it throws a **402 Payment Required** error.
    - **Update**: We modified this to include `{ scheme: "streaming" }` in the error details, telling the Agent: *"I accept CronosStream Vouchers."*

---

## 3. The Sequencer (`sequencer/`)
*The "Validator" - Off-chain ledger.*

### `src/service.rs`
**Role**: The Brain.
- **Key Logic**:
    - **`settle()`**: Receives a voucher.
    - **Validation**:
        1. Checks `signature`: Did the Agent actually sign this?
        2. Checks `balance`: Does `amount <= deposited_balance`?
        3. Checks `sequence`: Is this the next valid number (n+1)?
    - **Co-Signing**: If valid, the Sequencer **Co-Signs** the state update. This double-signature (Agent + Sequencer) is what allows the channel to be closed on-chain disputes if needed.
    - **Persistence**: Updates the internal database so the Agent can't double-spend.

### `src/crypto.rs`
**Role**: Cryptography.
- **Key Logic**:
    - Implements the **EIP-712 Hashing** logic exactly matching the Solidity contract.
    - **Fix**: This is where we updated the Domain Name to `StreamChannel` to ensure the off-chain signatures match what the on-chain contract expects.

---

## Summary
We have successfully built a closed loop:
1.  **Agent** (`channel_manager.py`) signs a voucher.
2.  **Resource** (`resource.controller.ts`) receives it.
3.  **Sequencer** (`service.rs`) validates it against the on-chain deposit.
4.  **Resource** unlocks the data.

All of this happens off-chain, enabling the high-frequency trading bot use case.
