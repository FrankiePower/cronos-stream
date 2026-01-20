What the Sequencer Does
The sequencer is an off-chain service that sits between clients and the smart contract. It's the "trusted middleman" that:

Core Responsibilities

┌──────────┐     voucher      ┌────────────┐     on-chain     ┌──────────────┐
│  Client  │ ───────────────▶ │ Sequencer  │ ───────────────▶ │ StreamChannel│
│ (Payer)  │                  │  Service   │                  │   Contract   │
└──────────┘                  └────────────┘                  └──────────────┘
     │                              │
     │ signs voucher                │ validates signature
     │ (EIP-712)                    │ co-signs voucher
     │                              │ stores state in DB
     │                              │ can finalize on-chain
API Endpoints
Endpoint	Purpose
POST /channel/seed	Register a new channel (after user opens on-chain)
GET /channel/:id	Get channel state
POST /validate	Validate a payment voucher (read-only, no state change)
POST /settle	Accept a payment voucher (updates state, co-signs)
POST /channel/finalize	Close channel on-chain (calls smart contract)
GET /channels/by-owner/:owner	List user's channels
File Structure (Reference)
File	Purpose
main.rs	Entry point - loads config, connects DB, starts server
model.rs	Data structures (ChannelState, Request/Response types)
handlers.rs	HTTP route handlers (thin layer)
service.rs	Business logic (validation, state updates)
crypto.rs	EIP-712 signature verification and signing
db.rs	PostgreSQL persistence
config.rs	Environment variable loading
error.rs	Error types
Let's Build It From Scratch
