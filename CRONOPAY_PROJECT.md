# CronoPay: Autonomous AI Agent Platform

> **Tagline**: "AI agents that manage your money while you sleep"
>
> **Not a payment gateway. An agent marketplace.**

## 🎯 Project Vision

CronoPay is the first **Autonomous AI Agent Platform** on Cronos that combines:
- 🤖 **Autonomous AI agents** that proactively manage your finances
- ⚡ **x402 micropayments** for pay-per-use agent execution fees
- 💱 **DeFi integration** (VVS Finance) for automated trading/rebalancing
- 🔗 **Agent discovery protocol** enabling decentralized agent ecosystem
- 💳 **Hybrid payment rails** (crypto + Stripe) for mainstream adoption

**The Problem**: People waste money on unused subscriptions, miss optimal DeFi opportunities, and manually manage finances.

**The Solution**: Install AI agents that autonomously manage subscriptions, execute DeFi strategies, and optimize spending - agents pay themselves via x402.

---

## ❓ How is CronoPay Different from Crypto.com Pay?

**Crypto.com Pay**: Payment gateway for merchants (like Stripe for crypto)
- 👤 Human manually checks out
- 🏪 Merchant receives payment
- 📱 User scans QR, confirms each time
- 🎯 Use case: Buying products at checkout

**CronoPay**: AI agent platform for consumers
- 🤖 AI agents execute autonomously
- 💰 Agents pay other agents via x402
- ⚡ Set rules once, agents handle rest
- 🎯 Use case: Agents managing your finances

**Key insight**: We might actually **use** Crypto.com Pay as one payment method, but we solve a completely different problem - autonomous financial management, not checkout.

---

## 🏆 Hackathon Strategy

### **Target Tracks**
1. **Main Track** - x402 Applications (Primary)
2. **Agentic Finance Track** - Advanced programmatic settlement
3. **Crypto.com Ecosystem Integration** - Stripe + Crypto.com Pay

### **Winning Thesis**
- ✅ **Real utility**: Solves actual problems (subscription waste, DeFi complexity)
- ✅ **Real integrations**: Stripe, Crypto.com, VVS Finance, Cronos EVM
- ✅ **x402 done right**: Micropayments for agent services (not forced)
- ✅ **Mainstream appeal**: Works with Stripe cards (no wallet knowledge needed)
- ✅ **Ecosystem play**: Platform enables 3rd party agents (network effects)
- ✅ **Technical depth**: A2A discovery, x402 protocol, smart contract wallets

---

## 🏗️ System Architecture

### **High-Level Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    CronoPay Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Frontend (Mobile PWA)                        │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • React + Vite + PWA                                │  │
│  │  • Agent Marketplace UI                              │  │
│  │  • User Dashboard                                    │  │
│  │  • Payment Management                                │  │
│  │  • Real-time Activity Feed                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↕                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Backend (Platform Services)                  │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • Node.js + Express + TypeScript                    │  │
│  │  • Agent Registry & Discovery                        │  │
│  │  • User Account Management                           │  │
│  │  • Payment Service (Unified)                         │  │
│  │  • x402 Settlement Handler                           │  │
│  │  • Stripe Integration                                │  │
│  │  • WebSocket Server (real-time)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↕                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Agent Services (1st Party)                   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • Subscription Manager AI (Python)                  │  │
│  │  • VVS Finance Trading AI (Python)                   │  │
│  │  • Portfolio Rebalancer AI (Python)                  │  │
│  │  • Each exposes /.well-known/agent-card.json        │  │
│  │  • Each has x402-protected endpoints                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│              External Integrations                          │
├─────────────────────────────────────────────────────────────┤
│  • Cronos EVM (x402 settlements)                            │
│  • VVS Finance (DEX swaps)                                  │
│  • Stripe (card payments & top-ups)                         │
│  • Crypto.com Pay (optional: OAuth + balance)               │
│  • Crypto.com Market Data MCP (price feeds)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Core Concepts

### **1. Agent Marketplace**
- Users browse and install AI agents (like an app store)
- Each agent performs specific automated tasks
- Agents are discovered via **Agent Cards** (/.well-known/agent-card.json)
- Open platform: 3rd parties can build and register agents

### **2. Hybrid Payment Rails**
Users can fund their account with:
- **Crypto**: Deposit USDC/CRO to Cronos wallet
- **Stripe Card**: Add funds via credit/debit card
- **Crypto.com Balance**: Connect Crypto.com account (future)

The platform automatically converts between rails as needed.

### **3. x402 Micropayments**
- Every agent execution requires x402 payment
- Pay-per-use model (no subscriptions)
- Typical fees: 0.01 - 0.10 USDC per execution
- Settled on Cronos EVM using facilitator SDK
- **Key insight**: x402 pays for AGENT SERVICE, not underlying actions

### **4. Agent Discovery Protocol**
Based on A2A (Agent-to-Agent) standard:
- Each agent hosts public JSON at `/.well-known/agent-card.json`
- Describes available services, pricing, and x402 endpoints
- Platform aggregates agent cards into marketplace
- Enables decentralized agent ecosystem

---

## 🤖 Example Agents

### **1. Subscription Manager AI**
**Problem**: Average person wastes $74/month on unused subscriptions

**What it does**:
- Analyzes linked bank/card transactions
- Detects recurring subscriptions
- Checks actual usage patterns
- Recommends cancellations
- Can auto-cancel unused subscriptions

**x402 Pricing**:
- Analysis: 0.05 USDC per scan
- Cancel subscription: 0.10 USDC per cancellation

**Agent Card**: `https://sub-manager.cronopay.app/.well-known/agent-card.json`

**Protected Endpoints**:
- `POST /api/analyze` (x402 protected)
- `POST /api/cancel` (x402 protected)
- `GET /api/status` (free)

---

### **2. VVS Finance Trading AI**
**Problem**: Users miss DeFi opportunities, poor timing, high fees

**What it does**:
- Executes DCA (dollar-cost averaging) strategies
- Monitors prices and executes limit orders
- Finds optimal swap routes on VVS Finance
- Auto-compounds LP rewards

**x402 Pricing**:
- DCA execution: 0.01 USDC per swap
- Limit order: 0.05 USDC per execution
- Auto-compound: 0.02 USDC per compound

**Agent Card**: `https://vvs-trader.cronopay.app/.well-known/agent-card.json`

**Protected Endpoints**:
- `POST /api/dca/execute` (x402 protected)
- `POST /api/limit-order` (x402 protected)
- `POST /api/compound` (x402 protected)
- `GET /api/quote` (free)

---

### **3. Portfolio Rebalancer AI**
**Problem**: Crypto portfolios drift from targets, manual rebalancing is tedious

**What it does**:
- Monitors portfolio allocation 24/7
- Detects drift from target percentages
- Executes rebalancing swaps on VVS Finance
- Optimizes for gas fees and slippage

**x402 Pricing**:
- Rebalance execution: 0.05 USDC per rebalance
- Portfolio analysis: 0.01 USDC per check

**Agent Card**: `https://rebalancer.cronopay.app/.well-known/agent-card.json`

**Protected Endpoints**:
- `POST /api/rebalance` (x402 protected)
- `GET /api/analyze` (x402 protected)
- `GET /api/status` (free)

---

## 🔄 User Flows

### **Flow 1: Onboarding (New User)**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (PWA)
    participant B as Backend
    participant S as Stripe

    U->>F: Opens CronoPay app
    F->>U: Welcome screen
    U->>F: "Sign Up"
    F->>U: Choose sign-up method

    alt Stripe Card
        U->>F: "Connect Stripe Card"
        F->>S: Create checkout session
        S->>U: Card input form
        U->>S: Enters card details
        S->>F: Card saved (payment method ID)
        F->>B: Create user account + save payment method
    else Crypto Deposit
        U->>F: "Deposit Crypto"
        B->>U: Shows wallet address + QR code
        U->>B: Sends USDC to address
    else Crypto.com OAuth
        U->>F: "Connect Crypto.com"
        F->>B: Initiate OAuth
        B->>U: Redirects to Crypto.com
        U->>B: Approves connection
    end

    B->>U: Account created ✅
    F->>U: Shows "Add Funds" screen
    U->>F: Adds $50
    F->>U: Shows Marketplace
```

---

### **Flow 2: Installing & Using Agent**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant R as Agent Registry
    participant A as Agent Service
    participant X as x402 Facilitator
    participant C as Cronos EVM

    U->>F: Browse marketplace
    F->>B: GET /api/agents
    B->>R: Fetch registered agents
    R->>B: Agent list

    loop Discovery
        B->>A: GET /.well-known/agent-card.json
        A->>B: Agent card (services, pricing)
    end

    B->>F: Agents with metadata
    F->>U: Shows marketplace

    U->>F: Selects "Subscription Manager"
    F->>U: Shows agent details
    U->>F: Clicks "Install"

    F->>B: POST /api/user-agents/install
    B->>B: Creates user_agent record
    B->>F: Installation success

    F->>U: "Configure Agent"
    U->>F: Grants permissions, sets params
    U->>F: "Execute Analysis"

    F->>B: POST /api/agents/:id/execute
    B->>B: Check user balance (has 45 USDC)

    B->>A: POST /api/analyze (no payment yet)
    A->>B: 402 Payment Required + x402 challenge

    B->>B: Generate x402 payment header
    B->>X: Sign payment (0.05 USDC)
    X->>B: Payment header (Base64)

    B->>A: POST /api/pay
    A->>X: Verify payment header
    X->>C: Settle payment on-chain
    C->>X: Transaction hash
    X->>A: Payment verified ✅
    A->>B: Payment ID

    B->>A: POST /api/analyze (with payment ID)
    A->>A: Execute analysis
    A->>B: Results

    B->>B: Deduct 0.05 USDC from user balance
    B->>F: Analysis complete + results
    F->>U: Shows subscription analysis
```

---

### **Flow 3: Automatic Agent Execution**

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant B as Backend
    participant U as User Wallet
    participant A as Agent Service
    participant V as VVS Finance
    participant C as Cronos EVM

    Note over S: Cron job runs every hour

    S->>B: Check scheduled agents
    B->>B: Find "DCA Agent" due for execution

    B->>U: Check balance (has 50 USDC)

    B->>A: POST /api/dca/execute (via x402 flow)
    Note over B,A: x402 payment (0.01 USDC)

    A->>V: Calculate best swap route
    V->>A: Quote: 10 USDC → 145.3 CRO

    A->>C: Execute swap on VVS
    C->>A: Transaction hash

    A->>B: Execution result
    B->>B: Log execution, deduct fee

    B->>U: Push notification
    Note over U: "DCA executed: Bought 145.3 CRO"
```

---

## 💳 Payment Architecture

### **Payment Rails Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Payment Methods                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Cronos Wallet                                           │
│     ├─ USDC Balance: 45.23                                  │
│     ├─ CRO Balance: 1,234.56                                │
│     └─ Wallet Address: 0xabc...                             │
│                                                             │
│  2. CronoPay USD Balance                                    │
│     ├─ USD Balance: $12.34                                  │
│     └─ (Held in platform, can auto-convert to crypto)      │
│                                                             │
│  3. Saved Stripe Card                                       │
│     ├─ Visa •••• 4242                                       │
│     ├─ Can charge for auto top-ups                          │
│     └─ Off-session payments enabled                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Payment Priority Waterfall**

When agent needs to execute (requires payment):

```
1. Check Crypto Balance (USDC)
   └─ Sufficient? → Use x402 payment → Execute ✅

2. Check USD Balance
   └─ Sufficient? → Convert USD→USDC → Use x402 → Execute ✅

3. Check Saved Card
   └─ Available? → Charge card → Credit balance → Execute ✅

4. Insufficient Funds
   └─ Notify user → Prompt to add funds ❌
```

### **x402 Payment Flow Detail**

```typescript
// When agent execution is requested
async function executeAgent(userId, agentId, params) {
  // 1. Get agent details (including fees)
  const agent = await getAgentFromRegistry(agentId);
  const executionFee = parseFloat(agent.executionFee.amount) / 1e6; // 0.05 USDC

  // 2. Ensure user has sufficient balance
  await ensureSufficientBalance(userId, executionFee);

  // 3. Call agent's protected endpoint
  const response = await fetch(agent.endpoints.execute, {
    method: 'POST',
    body: JSON.stringify(params)
  });

  // 4. Agent returns 402 Payment Required
  if (response.status === 402) {
    const challenge = await response.json();
    // {
    //   "x402Version": 1,
    //   "error": "payment_required",
    //   "accepts": [{
    //     "scheme": "exact",
    //     "network": "cronos-testnet",
    //     "payTo": "0xAGENT_ADDRESS",
    //     "asset": "0xUSDC_CONTRACT",
    //     "maxAmountRequired": "50000", // 0.05 USDC
    //     "maxTimeoutSeconds": 300,
    //     "extra": { "paymentId": "pay_abc123" }
    //   }]
    // }

    // 5. Generate x402 payment header
    const userWallet = await getUserWallet(userId);
    const facilitator = new Facilitator({ network: 'cronos-testnet' });

    const paymentHeader = await facilitator.generatePaymentHeader({
      to: challenge.accepts[0].payTo,
      value: challenge.accepts[0].maxAmountRequired,
      signer: userWallet,
      validBefore: Math.floor(Date.now() / 1000) + 300,
      validAfter: 0
    });

    // 6. Submit payment for settlement
    const paymentResponse = await fetch(agent.paywall.settlement, {
      method: 'POST',
      body: JSON.stringify({
        paymentId: challenge.accepts[0].extra.paymentId,
        paymentHeader: paymentHeader,
        paymentRequirements: challenge.accepts[0]
      })
    });

    // 7. Agent verifies & settles payment on-chain
    const settlement = await paymentResponse.json();
    // { "ok": true, "txHash": "0x..." }

    // 8. Retry original request with payment ID
    const finalResponse = await fetch(agent.endpoints.execute, {
      method: 'POST',
      headers: {
        'x-payment-id': challenge.accepts[0].extra.paymentId
      },
      body: JSON.stringify(params)
    });

    // 9. Get results
    const result = await finalResponse.json();

    // 10. Deduct fee from user's balance
    await deductBalance(userId, executionFee);

    return result;
  }
}
```

---

## 🔍 Agent Discovery Protocol

### **Agent Card Specification**

Every agent MUST host a public JSON file at:
```
https://<agent-domain>/.well-known/agent-card.json
```

**Agent Card Schema**:

```json
{
  "version": "1.0",
  "name": "subscription-manager-ai",
  "displayName": "Subscription Manager AI",
  "description": "Analyzes and optimizes your subscription spending",
  "author": {
    "name": "CronoPay Team",
    "url": "https://cronopay.app",
    "contact": "hello@cronopay.app"
  },
  "category": "subscriptions",
  "tags": ["subscriptions", "finance", "automation", "savings"],
  "icon": "https://sub-manager.cronopay.app/icon.png",
  "url": "https://sub-manager.cronopay.app",
  "network": "cronos-testnet",
  "version": "1.2.0",
  "
": "1.2.0",

  "resources": [
    {
      "id": "analyze-subscriptions",
      "title": "Analyze Subscriptions",
      "description": "Scans linked accounts and analyzes subscription usage patterns",
      "url": "/api/analyze",
      "method": "POST",

      "paywall": {
        "protocol": "x402",
        "version": 1,
        "settlement": "/api/pay",
        "price": "50000",
        "currency": "USDC",
        "network": "cronos-testnet"
      },

      "parameters": {
        "linkedAccounts": {
          "type": "array",
          "description": "Array of linked account IDs",
          "required": true,
          "items": {
            "type": "string"
          }
        },
        "period": {
          "type": "string",
          "description": "Analysis period",
          "required": false,
          "default": "90d",
          "enum": ["30d", "90d", "180d", "1y"]
        }
      },

      "returns": {
        "type": "object",
        "properties": {
          "subscriptions": {
            "type": "array",
            "description": "List of detected subscriptions with recommendations"
          },
          "totalMonthlyCost": {
            "type": "number",
            "description": "Total monthly cost in USD"
          },
          "potentialSavings": {
            "type": "number",
            "description": "Potential monthly savings in USD"
          }
        }
      }
    },

    {
      "id": "cancel-subscription",
      "title": "Cancel Subscription",
      "description": "Attempts to cancel a subscription on your behalf",
      "url": "/api/cancel",
      "method": "POST",

      "paywall": {
        "protocol": "x402",
        "version": 1,
        "settlement": "/api/pay",
        "price": "100000",
        "currency": "USDC",
        "network": "cronos-testnet"
      },

      "parameters": {
        "subscriptionId": {
          "type": "string",
          "description": "ID of subscription to cancel",
          "required": true
        }
      },

      "returns": {
        "type": "object",
        "properties": {
          "success": {
            "type": "boolean"
          },
          "message": {
            "type": "string"
          },
          "refundAmount": {
            "type": "number",
            "description": "Prorated refund amount if applicable"
          }
        }
      }
    },

    {
      "id": "subscription-status",
      "title": "Get Subscription Status",
      "description": "Returns current status of monitored subscriptions",
      "url": "/api/status",
      "method": "GET",
      "paywall": null,

      "parameters": {},

      "returns": {
        "type": "object",
        "properties": {
          "monitored": {
            "type": "number",
            "description": "Number of subscriptions being monitored"
          },
          "lastUpdate": {
            "type": "string",
            "format": "date-time"
          }
        }
      }
    }
  ],

  "integrations": [
    "stripe",
    "plaid",
    "cronos-evm"
  ],

  "pricing": {
    "model": "pay-per-use",
    "currency": "USDC",
    "fees": {
      "analyze": "0.05",
      "cancel": "0.10"
    }
  },

  "stats": {
    "installs": 12543,
    "rating": 4.8,
    "reviews": 1203,
    "totalExecutions": 45232
  }
}
```

### **Discovery Process**

```typescript
// Platform's Agent Discovery Service

class AgentDiscoveryService {

  // Fetch and cache agent card
  async discoverAgent(agentUrl: string): Promise<AgentCard | null> {
    const wellKnownPaths = [
      '/.well-known/agent-card.json',
      '/.well-known/agent.json'
    ];

    for (const path of wellKnownPaths) {
      try {
        const response = await fetch(`${agentUrl}${path}`);
        if (response.ok) {
          const card = await response.json();

          // Validate card schema
          if (this.validateAgentCard(card)) {
            // Cache in database
            await this.cacheAgentCard(agentUrl, card);
            return card;
          }
        }
      } catch (error) {
        console.error(`Failed to fetch agent card from ${agentUrl}${path}`);
      }
    }

    return null;
  }

  // Discover all agents from registry
  async discoverAllAgents(): Promise<AgentCard[]> {
    // Get list of agent URLs from registry
    const agentUrls = await this.getRegisteredAgentUrls();

    // Fetch all agent cards in parallel
    const cards = await Promise.all(
      agentUrls.map(url => this.discoverAgent(url))
    );

    // Filter out failed discoveries
    return cards.filter(card => card !== null);
  }

  // Refresh agent cards periodically (every 1 hour)
  async refreshAgentCards() {
    const agents = await this.discoverAllAgents();
    console.log(`Discovered ${agents.length} agents`);
  }
}
```

---

## 🗄️ Database Schema

### **Users Table**

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Authentication
  auth_provider VARCHAR(50) NOT NULL, -- 'email', 'crypto.com', 'web3'
  crypto_com_user_id VARCHAR(255),

  -- Cronos Wallet
  wallet_address VARCHAR(42) NOT NULL UNIQUE,
  wallet_private_key_encrypted TEXT NOT NULL,

  -- Stripe
  stripe_customer_id VARCHAR(255) UNIQUE,

  -- Balances (cached, source of truth is on-chain/stripe)
  balance_usd DECIMAL(18, 2) DEFAULT 0.00,
  balance_usdc DECIMAL(18, 6) DEFAULT 0.000000,
  balance_cro DECIMAL(18, 6) DEFAULT 0.000000,

  -- Settings
  settings JSONB DEFAULT '{}',

  -- Status
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'deleted'

  INDEX idx_email (email),
  INDEX idx_wallet (wallet_address),
  INDEX idx_stripe (stripe_customer_id)
);
```

### **Payment Methods Table**

```sql
CREATE TABLE payment_methods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Type
  type VARCHAR(20) NOT NULL, -- 'card', 'crypto'

  -- Stripe Card
  stripe_payment_method_id VARCHAR(255),
  card_brand VARCHAR(20), -- 'visa', 'mastercard', 'amex'
  card_last4 VARCHAR(4),
  card_exp_month INTEGER,
  card_exp_year INTEGER,

  -- Crypto Wallet (if external)
  wallet_address VARCHAR(42),
  wallet_network VARCHAR(50),

  -- Status
  is_default BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,

  INDEX idx_user (user_id),
  INDEX idx_stripe_pm (stripe_payment_method_id)
);
```

### **Agents Table** (Registry)

```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Identity
  name VARCHAR(100) NOT NULL UNIQUE, -- 'subscription-manager-ai'
  display_name VARCHAR(200) NOT NULL, -- 'Subscription Manager AI'
  description TEXT,

  -- Discovery
  agent_url VARCHAR(500) NOT NULL UNIQUE,
  agent_card_url VARCHAR(500) NOT NULL,
  agent_card JSONB NOT NULL, -- Full agent card JSON

  -- Categorization
  category VARCHAR(50), -- 'subscriptions', 'trading', 'defi'
  tags TEXT[], -- {'subscriptions', 'finance', 'automation'}

  -- Author
  author_name VARCHAR(200),
  author_url VARCHAR(500),
  author_contact VARCHAR(255),

  -- Pricing
  execution_fee_amount BIGINT NOT NULL, -- In base units (e.g., 50000 = 0.05 USDC)
  execution_fee_currency VARCHAR(10) NOT NULL, -- 'USDC', 'CRO'

  -- Stats (cached, updated periodically)
  total_installs INTEGER DEFAULT 0,
  total_executions BIGINT DEFAULT 0,
  average_rating DECIMAL(3, 2) DEFAULT 0.00,
  total_reviews INTEGER DEFAULT 0,

  -- Status
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'deprecated'
  is_verified BOOLEAN DEFAULT FALSE, -- Official/verified agents
  is_featured BOOLEAN DEFAULT FALSE,

  -- Metadata
  version VARCHAR(20),
  icon_url VARCHAR(500),
  network VARCHAR(50), -- 'cronos-testnet', 'cronos-mainnet'

  INDEX idx_category (category),
  INDEX idx_status (status),
  INDEX idx_featured (is_featured),
  INDEX idx_name (name)
);
```

### **User Agents Table** (Installed Agents)

```sql
CREATE TABLE user_agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Configuration
  config JSONB DEFAULT '{}', -- Agent-specific config

  -- Scheduling
  schedule VARCHAR(100), -- Cron expression, e.g., "0 9 * * 1" (Mon 9am)
  schedule_enabled BOOLEAN DEFAULT FALSE,

  -- Status
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'error'

  -- Stats
  total_executions INTEGER DEFAULT 0,
  total_fees_paid DECIMAL(18, 6) DEFAULT 0.000000,
  last_executed_at TIMESTAMP,
  last_error TEXT,

  UNIQUE(user_id, agent_id),
  INDEX idx_user (user_id),
  INDEX idx_agent (agent_id),
  INDEX idx_schedule (schedule_enabled, schedule)
);
```

### **Agent Executions Table**

```sql
CREATE TABLE agent_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_agent_id UUID NOT NULL REFERENCES user_agents(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,

  -- Execution details
  status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'

  -- Payment
  payment_id VARCHAR(100) UNIQUE,
  payment_amount DECIMAL(18, 6), -- Fee paid in USDC
  payment_tx_hash VARCHAR(66), -- Cronos transaction hash

  -- Request/Response
  request_params JSONB,
  response_data JSONB,

  -- Error handling
  error_message TEXT,
  error_code VARCHAR(50),

  -- Timing
  duration_ms INTEGER, -- Execution time in milliseconds

  INDEX idx_user_agent (user_agent_id),
  INDEX idx_status (status),
  INDEX idx_payment (payment_id),
  INDEX idx_created (created_at DESC)
);
```

### **Transactions Table** (Financial Ledger)

```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),

  -- Transaction type
  type VARCHAR(50) NOT NULL, -- 'deposit', 'withdrawal', 'agent_fee', 'top_up', 'conversion'

  -- Amounts
  amount DECIMAL(18, 6) NOT NULL,
  currency VARCHAR(10) NOT NULL, -- 'USD', 'USDC', 'CRO'

  -- Related entities
  agent_execution_id UUID REFERENCES agent_executions(id),
  payment_method_id UUID REFERENCES payment_methods(id),

  -- Blockchain
  tx_hash VARCHAR(66), -- On-chain transaction hash
  network VARCHAR(50), -- 'cronos-testnet', 'cronos-mainnet'

  -- Stripe
  stripe_payment_intent_id VARCHAR(255),
  stripe_charge_id VARCHAR(255),

  -- Balance changes
  balance_before DECIMAL(18, 6),
  balance_after DECIMAL(18, 6),

  -- Metadata
  description TEXT,
  metadata JSONB DEFAULT '{}',

  INDEX idx_user (user_id),
  INDEX idx_type (type),
  INDEX idx_created (created_at DESC),
  INDEX idx_tx_hash (tx_hash)
);
```

---

## 🛠️ Technology Stack

### **Frontend (Mobile PWA)**
- **Framework**: React 18
- **Build Tool**: Vite 7
- **Styling**: Styled Components
- **State Management**: React Context + Zustand (for complex state)
- **Routing**: React Router 6
- **PWA**: vite-plugin-pwa
- **Wallet**: MetaMask SDK, WalletConnect
- **HTTP Client**: Fetch API with custom wrapper
- **Real-time**: WebSocket (native)
- **Charts**: Recharts or Chart.js

### **Backend (Platform Services)**
- **Runtime**: Node.js 20+
- **Framework**: Express 4
- **Language**: TypeScript 5
- **Database**: PostgreSQL 15 (or SQLite for MVP)
- **ORM**: Prisma or raw SQL
- **Authentication**: JWT + OAuth2
- **WebSocket**: ws library
- **Cron Jobs**: node-cron
- **Logging**: Winston
- **Validation**: Zod

### **Agent Services (Python)**
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **HTTP Server**: Uvicorn
- **HTTP Client**: httpx
- **Blockchain**: web3.py, eth-account
- **x402**: @crypto.com/facilitator-client (via subprocess or REST)
- **Async**: asyncio
- **LLM** (optional): OpenAI SDK

### **Blockchain & Payments**
- **Blockchain**: Cronos EVM (Testnet → Mainnet)
- **x402 Protocol**: @crypto.com/facilitator-client v1.0.1
- **Payments**: Stripe API v2023+
- **Wallet**: ethers.js v6 or viem
- **DEX**: VVS Finance SDK
- **Market Data**: Crypto.com Market Data MCP (optional)

### **DevOps & Infrastructure**
- **Hosting**: Vercel (frontend), Railway/Fly.io (backend)
- **Database**: Neon.tech (PostgreSQL) or Turso (SQLite)
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry (errors), PostHog (analytics)
- **Domain**: Namecheap or Cloudflare

---

## 📅 Development Roadmap

### **Phase 1: MVP Foundation** (Week 1: Jan 13-19)

**Goals**: Core platform + 1 working agent

**Tasks**:
- [ ] Project setup (monorepo structure)
- [ ] Database schema implementation
- [ ] User authentication (email/password)
- [ ] Wallet creation (Cronos testnet)
- [ ] Stripe integration (add funds via card)
- [ ] Agent registry (hardcoded 1 agent for now)
- [ ] Build Subscription Manager Agent
  - [ ] Agent card JSON
  - [ ] x402 middleware
  - [ ] Mock subscription analysis logic
- [ ] Frontend: Marketplace page (1 agent)
- [ ] Frontend: Agent detail page
- [ ] Frontend: User dashboard
- [ ] End-to-end test: Install agent → Execute → See results

**Deliverable**: Working demo with 1 agent

---

### **Phase 2: Multi-Agent + Real Integrations** (Week 2: Jan 20-26)

**Goals**: 3 agents + VVS Finance integration

**Tasks**:
- [ ] Build VVS Finance Trading Agent
  - [ ] VVS Finance SDK integration
  - [ ] DCA strategy implementation
  - [ ] Limit orders
  - [ ] Quote endpoint
- [ ] Build Portfolio Rebalancer Agent
  - [ ] Portfolio analysis logic
  - [ ] Rebalancing algorithm
  - [ ] VVS Finance integration
- [ ] Agent discovery automation
  - [ ] Fetch agent cards from URLs
  - [ ] Validate agent card schema
  - [ ] Cache in database
- [ ] Payment waterfall logic
  - [ ] Check crypto balance
  - [ ] Auto-convert USD → USDC
  - [ ] Charge saved card if needed
- [ ] Scheduled agent execution
  - [ ] Cron job service
  - [ ] Execute agents on schedule
- [ ] Real-time activity feed
  - [ ] WebSocket server
  - [ ] Push notifications to frontend
- [ ] Frontend: 3 agents in marketplace
- [ ] Frontend: Agent configuration UI
- [ ] Frontend: Activity feed component

**Deliverable**: 3 working agents, real VVS swaps

---

### **Phase 3: Polish + Demo** (Week 3: Jan 27 - Feb 2)

**Goals**: Production-ready, beautiful UI, demo video

**Tasks**:
- [ ] UI/UX polish
  - [ ] Beautiful marketplace design
  - [ ] Smooth animations
  - [ ] Mobile-first responsive
  - [ ] Loading states, error handling
- [ ] Analytics dashboard
  - [ ] Total savings
  - [ ] Agent performance
  - [ ] Fee breakdown
- [ ] Advanced features
  - [ ] Agent reviews & ratings
  - [ ] Multi-wallet support
  - [ ] Transaction history
- [ ] Testing
  - [ ] End-to-end tests
  - [ ] Real testnet transactions
  - [ ] Edge cases
- [ ] Documentation
  - [ ] User guide
  - [ ] Agent development guide
  - [ ] API documentation
- [ ] Deploy to production
  - [ ] Frontend → Vercel
  - [ ] Backend → Railway
  - [ ] Database → Neon
  - [ ] Custom domain
- [ ] Demo video (3-5 minutes)
  - [ ] Problem statement
  - [ ] Solution walkthrough
  - [ ] Live demo
  - [ ] Technical highlights
  - [ ] Future vision

**Deliverable**: Polished product + demo video

---

## 🎬 Demo Script (for Judges)

### **Act 1: The Problem** (30 seconds)
```
"Meet Sarah. She has 8 subscriptions.
Netflix, Spotify, Peloton, NYT, Disney+...

She barely uses Peloton ($44/mo) and never reads NYT ($17/mo).

That's $61/month wasted. $732/year.

She also wants to invest in crypto but finds it too complex.

What if AI could handle both?"
```

### **Act 2: The Solution** (60 seconds)
```
"This is CronoPay - your AI payment assistant.

[Open app]

Sarah signs up in 10 seconds.
Adds $50 with her Stripe card.

[Browse marketplace]

She installs Subscription Manager AI.
Costs 0.05 USDC per analysis.

[Configure & execute]

Agent scans her subscriptions.
Detects 3 unused subscriptions.
Recommends cancellations.

[Show results]

Potential savings: $74/month.

Sarah taps 'Cancel Unused'.
Agent executes via x402 micropayments.
Total cost: $0.35.

Done. She's saving $74/month.
```

### **Act 3: The Platform** (60 seconds)
```
[Show marketplace]

But that's just one agent.

[Scroll through agents]

• VVS Finance Trading AI - DCA into CRO
• Portfolio Rebalancer - Auto-rebalance
• Bill Negotiator - Negotiate better rates

Each agent:
- Autonomous execution
- x402 micropayments
- Pay-per-use (no subscriptions)

[Show VVS Trading Agent]

Sarah installs DCA Agent.
Sets: "Buy $20 CRO every Monday"

[Show scheduled execution]

Agent executes weekly.
Uses VVS Finance for swaps.
Pays 0.01 USDC per execution.

Sarah never touches a wallet.
Crypto becomes invisible.
```

### **Act 4: The Tech** (45 seconds)
```
[Show architecture diagram]

How it works:

1. Agent Discovery
   - Agents host public JSON cards
   - Platform discovers via /.well-known/agent-card.json
   - Decentralized, no central authority

2. x402 Micropayments
   - Every execution requires payment
   - EIP-3009 signed payments
   - Settled on Cronos EVM
   - Sub-cent fees

3. Hybrid Payment Rails
   - Crypto (Cronos wallet)
   - Stripe (credit cards)
   - Auto-conversion between rails

4. Real Integrations
   - VVS Finance (DEX swaps)
   - Stripe + Crypto.com (payments)
   - Cronos EVM (settlements)
```

### **Act 5: The Vision** (15 seconds)
```
[Show agent development guide]

CronoPay is a platform.

Anyone can build agents.
Register via agent card.
Earn x402 micropayments.

The future of payments is autonomous.
CronoPay makes it real.

Built on Cronos. Powered by x402.
```

**Total: 3 minutes 30 seconds**

---

## 🏅 Judging Criteria Alignment

### **Innovation** ✅
- **First** agent marketplace with x402 micropayments
- **First** hybrid payment rails (crypto + Stripe) for agents
- **First** "invisible crypto" for mainstream adoption
- **Novel** use of agent cards for discovery
- **Unique** business model (pay-per-use agents)

### **Agentic Functionality** ✅
- **Fully autonomous**: Agents execute without human intervention
- **Multi-agent**: Multiple agents working in parallel
- **A2A commerce**: Agents discovering and calling other agents
- **Self-sovereign**: Users control agents, agents execute autonomously
- **Intelligent**: Agents make decisions (LLM-powered for analysis)

### **Execution Quality** ✅
- **Real integrations**: Stripe, VVS Finance, Cronos EVM, facilitator SDK
- **Production-quality code**: TypeScript, proper architecture, error handling
- **Working demo**: Real testnet transactions, real agent executions
- **Polished UI**: Mobile-first PWA, beautiful design
- **Complete**: Full stack (frontend, backend, agents, blockchain)

### **Ecosystem Value** ✅
- **Drives x402 adoption**: Real use case for micropayments
- **Drives Cronos adoption**: All settlements on Cronos
- **Drives Crypto.com adoption**: Stripe integration, potential OAuth
- **Drives VVS adoption**: Real DEX swaps via agents
- **Platform play**: Extensible, 3rd parties can build agents
- **Mainstream bridge**: Works with Stripe cards (150M+ addressable users)

---

## 📚 Resources & Links

### **Cronos & x402**
- [Cronos x402 Facilitator Docs](https://docs.cronos.org/cronos-x402-facilitator/introduction)
- [Facilitator SDK (NPM)](https://www.npmjs.com/package/@crypto.com/facilitator-client)
- [x402 Examples Repository](https://github.com/cronos-labs/x402-examples)
- [Cronos Testnet Faucet](https://cronos.org/faucet)
- [devUSDC.e Faucet](https://faucet.cronos.org)

### **VVS Finance**
- [VVS Finance SDK](https://github.com/vvs-finance/swap-sdk)
- [VVS Info API Docs](https://github.com/vvs-finance/vvs-ui/blob/master/packages/vvs-info-api/documentation.md)
- [VVS Finance App](https://vvs.finance/)

### **Stripe**
- [Stripe + Crypto.com Partnership](https://crypto.com/us/company-news/cryptocom-and-stripe-partner-to-enable-better-crypto-payments)
- [Stripe Connect Docs](https://docs.stripe.com/connect/how-connect-works)
- [Stripe Payment Methods](https://docs.stripe.com/payments/save-and-reuse)
- [Stripe API Reference](https://docs.stripe.com/api)

### **Crypto.com**
- [Crypto.com Pay Docs](https://pay-docs.crypto.com/)
- [Crypto.com OAuth (Exchange)](https://crypto.com/en/product-news/fastapi-and-oauth-2)
- [Crypto.com Market Data MCP](https://mcp.crypto.com/docs)

### **Hackathon**
- [Cronos x402 Paytech Hackathon (DoraHacks)](https://dorahacks.io/hackathon/cronos-x402)
- [Cronos Discord (x402-hackathon channel)](https://discord.com/channels/783264383978569728/1442807140103487610)
- [Cronos Developers Telegram](https://t.me/+1lyRjf6x5eQ5NzVl)

### **Development Tools**
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Express Documentation](https://expressjs.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ethers.js Documentation](https://docs.ethers.org/v6/)

---

## 🚀 Getting Started (for Developers)

### **Prerequisites**
- Node.js 20+
- Python 3.10+
- PostgreSQL 15+ (or SQLite for local dev)
- Cronos testnet wallet with TCRO & devUSDC.e
- Stripe account (test mode)
- OpenAI API key (optional, for LLM features)

### **Initial Setup**

```bash
# Clone repository
git clone https://github.com/your-org/cronopay.git
cd cronopay

# Install dependencies
npm install  # Root dependencies
cd frontend && npm install
cd ../backend && npm install
cd ../agents/subscription-manager && pip install -r requirements.txt

# Copy environment files
cp .env.example .env
# Edit .env with your keys

# Setup database
cd backend
npx prisma migrate dev

# Start development servers
npm run dev  # Starts all services concurrently
```

### **Environment Variables**

```bash
# Backend (.env)
DATABASE_URL="postgresql://user:pass@localhost:5432/cronopay"
JWT_SECRET="your-secret-key"
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
CRONOS_NETWORK="cronos-testnet"
MERCHANT_ADDRESS="0x..."

# Frontend (.env)
VITE_API_BASE="http://localhost:3000"
VITE_STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Agents (.env)
X402_PRIVATE_KEY="0x..."
OPENAI_API_KEY="sk-..."
AGENT_PORT="9001"
```

---

## 📝 Contributing

This is a hackathon project, but we welcome contributions!

### **Agent Development Guide**
Want to build an agent for CronoPay? Follow these steps:

1. **Create agent card** (`/.well-known/agent-card.json`)
2. **Implement x402 middleware** (protect endpoints)
3. **Define endpoints** (`/api/execute`, `/api/status`)
4. **Test locally** with CronoPay platform
5. **Deploy agent** to public URL
6. **Register** agent URL in CronoPay registry

Full guide: [docs/AGENT_DEVELOPMENT.md](./docs/AGENT_DEVELOPMENT.md)

---

## 📄 License

MIT License - See [LICENSE](./LICENSE)

---

## 🙏 Acknowledgments

- **Cronos Labs** - For x402 protocol and facilitator SDK
- **Crypto.com** - For Stripe integration and ecosystem support
- **VVS Finance** - For DEX infrastructure on Cronos
- **Stripe** - For payment infrastructure
- **A2A Protocol** - For agent discovery inspiration

---

## 📞 Contact

- **Team**: CronoPay Team
- **Email**: hello@cronopay.app
- **Twitter**: [@CronoPay](https://twitter.com/cronopay)
- **Discord**: [Join our server](https://discord.gg/cronopay)
- **GitHub**: [github.com/cronopay](https://github.com/cronopay)

---

**Built for Cronos x402 Paytech Hackathon**
**Submission Date**: February 2026

---

*Last Updated: January 13, 2026*
