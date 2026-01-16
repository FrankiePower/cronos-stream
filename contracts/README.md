# CronosStream Smart Contracts

Payment channel smart contracts for CronosStream - enabling high-throughput micropayments on Cronos.

## Contracts

| Contract | Description |
|----------|-------------|
| `StreamChannel.sol` | Payment channel with EIP-712 signatures, sequencer co-signing, and multi-recipient support |
| `TUSDC.sol` | Test USDC token for local development (6 decimals) |

## Deployed Addresses (Cronos Testnet)

| Contract | Address |
|----------|---------|
| StreamChannel | `0xE118E04431853e9df5390E1AACF36dEF6A7a0254` |
| devUSDC.e (external) | `0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0` |

View on Explorer: https://explorer.cronos.org/testnet/address/0xE118E04431853e9df5390E1AACF36dEF6A7a0254

## Setup

```bash
npm install
```

## Development

### Compile Contracts

```bash
npx hardhat compile
```

### Run Tests

```bash
npx hardhat test
```

### Local Deployment

```bash
npx hardhat ignition deploy ./ignition/modules/StreamChannel.ts --network hardhatMainnet --parameters ./ignition/parameters-cronos.json
```

## Cronos Deployment

### Prerequisites

1. Set your private key:
```bash
npx hardhat keystore set CRONOS_PRIVATE_KEY
```

2. Get testnet CRO from: https://cronos.org/faucet

### Deploy to Testnet

Using existing devUSDC.e token:
```bash
npx hardhat ignition deploy ./ignition/modules/StreamChannelOnly.ts --network cronosTestnet --parameters ./ignition/parameters-cronos.json
```

### Deploy to Mainnet

```bash
npx hardhat ignition deploy ./ignition/modules/StreamChannelOnly.ts --network cronosMainnet --parameters ./ignition/parameters-cronos.json
```

## Contract Verification

1. Get an API key from: https://explorer-api-doc.cronos.org/testnet/

2. Store the API key:
```bash
npx hardhat keystore set CRONOS_EXPLORER_API_KEY
```

3. Verify:
```bash
npx hardhat verify --network cronosTestnet CONTRACT_ADDRESS "TOKEN_ADDRESS" "SEQUENCER_ADDRESS"
```

## Architecture

```
┌─────────────┐     deposit tokens     ┌─────────────────┐
│   Payer     │ ──────────────────────▶│  StreamChannel  │
│  (Agent A)  │                        │    Contract     │
└─────────────┘                        └────────┬────────┘
                                                │
      vouchers (off-chain)                      │ on close
         ┌──────────────────┐                   │
         │                  ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    distribute tokens
    │  Sequencer  │    │  Recipient  │ ◀──────────────────
    │             │    │  (Agent B)  │
    └─────────────┘    └─────────────┘
```

### Key Features

- **Channel Opening**: Lock tokens with EIP-712 signature
- **Off-chain Payments**: Sign vouchers without gas costs
- **Sequencer Co-signing**: Fraud prevention via dual signatures
- **Batch Settlement**: Close multiple channels in one transaction
- **Expiry Protection**: Anyone can close expired channels

## Networks

| Network | Chain ID | RPC URL |
|---------|----------|---------|
| Cronos Testnet | 338 | https://evm-t3.cronos.org/ |
| Cronos Mainnet | 25 | https://evm.cronos.org/ |

## License

UNLICENSED
