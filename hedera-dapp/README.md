# Hedera-Polymarket A2A Agent

Cross-chain AI agent that connects Hedera network with Polymarket hedge agent via A2A protocol.

## Overview

This agent enables:
- 🔗 **A2A Communication** via Hedera Consensus Service (HCS)
- 🤖 **Multi-agent coordination** between Hedera and Polymarket
- 💰 **Settlement** on Hedera using HTS/HBAR
- 📊 **Automated hedging** via Polymarket strategy

## Architecture

```
Hedera Agent (Node.js)
  ↓ HCS Topic (A2A messages)
  ↓ HTTP API call
Polymarket Agent (Python/Flask)
  ↓ Execute hedge strategy
  ↓ Return result
Hedera Agent
  ↓ Settle payment (HBAR transfer)
Hedera Testnet
```

## Setup

### 1. Get Hedera Testnet Account

1. Go to https://portal.hedera.com
2. Create free testnet account
3. Get 10,000 testnet HBAR
4. Copy your Account ID and Private Key

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```
HEDERA_ACCOUNT_ID=0.0.xxxxx
HEDERA_PRIVATE_KEY=302e020100...
POLYMARKET_API_URL=http://localhost:5001
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Start Polymarket API

In the parent directory:
```bash
cd ../polymarket-agent
python3 api.py
```

API should be running on http://localhost:5001

### 5. Run Hedera Agent

```bash
node agent.js
```

## Usage

### Basic Demo

The default `agent.js` runs a 3-step demo:

1. **Enter position** at 80% probability ($1000)
2. **Evaluate** at 86% probability (should recommend TAKE_PROFIT)
3. **Execute hedge** and settle 10 HBAR on Hedera

Expected output:
```
🚀 Initializing Hedera Agent...
✅ Connected to Hedera testnet
📍 Account ID: 0.0.xxxxx
💰 Balance: 10000 ℏ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMO 1: Enter Position at 80%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Calling Polymarket Agent: enter
✅ Polymarket response: ENTRY

💸 Settling payment on Hedera...
✅ Payment settled (status: SUCCESS)
   🔗 HashScan: https://hashscan.io/testnet/transaction/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMO 2: Evaluate Position at 86%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Calling Polymarket Agent: evaluate
✅ Polymarket response: TAKE_PROFIT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMO 3: Execute Hedge (Take Profit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Calling Polymarket Agent: hedge
✅ Polymarket response: HEDGE

💸 Settling payment on Hedera...
✅ Payment settled (status: SUCCESS)
   Transaction ID: 0.0.xxxxx@1700000000.000000000
   🔗 HashScan: https://hashscan.io/testnet/transaction/...

✅ Demo Complete!
```

### Programmatic Usage

```javascript
const { HederaPolymarketAgent } = require('./agent');

async function example() {
  const agent = new HederaPolymarketAgent();
  await agent.initialize();

  // Create HCS topic for A2A messages
  await agent.createA2ATopic();

  // Execute betting flow
  const result = await agent.executeBettingFlow({
    action: 'hedge',
    current_prob: 0.86,
    yes_price: 0.86,
    no_price: 0.14
  });

  console.log('Result:', result);
  await agent.close();
}
```

## API Methods

### `initialize()`
Connect to Hedera testnet and verify credentials.

### `createA2ATopic()`
Create HCS topic for A2A message logging.

### `sendA2AMessage(message)`
Send A2A message to HCS topic (verifiable, timestamped).

### `callPolymarketAgent(action, params)`
Call Polymarket hedge agent API.

Actions:
- `enter` - Open position
- `evaluate` - Get recommendation
- `hedge` - Execute hedge
- `exit` - Stop-loss exit

### `settlePayment(recipientId, amount, memo)`
Transfer HBAR on Hedera testnet.

### `executeBettingFlow(betProposal)`
Complete A2A flow: send message → call API → settle payment.

## A2A Message Format

Messages sent via HCS:
```json
{
  "type": "bet_proposal",
  "from": "0.0.xxxxx",
  "timestamp": "2025-11-21T19:30:00.000Z",
  "proposal": {
    "action": "hedge",
    "amount_usd": 1000,
    "current_prob": 0.86,
    "yes_price": 0.86,
    "no_price": 0.14
  }
}
```

## ETH Global Hackathon Qualifications

✅ **Multi-agent communication** - Hedera agent ↔ Polymarket agent via A2A
✅ **Hedera Agent Kit integration** - Uses `@hashgraph/sdk`
✅ **HCS for messaging** - A2A messages logged to consensus topic
✅ **HTS for settlement** - HBAR transfers on Hedera
✅ **Open-source** - MIT license

## Testing

### Test Hedera Connection Only
```javascript
const agent = new HederaPolymarketAgent();
await agent.initialize();
// Should print account balance
```

### Test Without HCS Topic
Comment out `await agent.createA2ATopic()` in `main()` to skip topic creation (faster demo).

### Test Without Settlement
Modify `executeBettingFlow()` to skip `settlePayment()` call.

## Troubleshooting

**Error: Missing Hedera credentials**
- Check `.env` file exists
- Verify `HEDERA_ACCOUNT_ID` and `HEDERA_PRIVATE_KEY` are set

**Error: Polymarket API error**
- Ensure `api.py` is running on port 5001
- Check `POLYMARKET_API_URL` in `.env`

**Error: Insufficient balance**
- Get free testnet HBAR at https://portal.hedera.com

**Port 5000 conflict (macOS AirPlay)**
- Polymarket API uses port 5001 instead

## Next Steps

- [ ] Add frontend UI (Phase 4)
- [ ] Implement real A2A negotiation with LLM
- [ ] Add AP2 payment protocol
- [ ] Multi-agent communication between multiple Hedera agents

## Resources

- Hedera Portal: https://portal.hedera.com
- HashScan Explorer: https://hashscan.io/testnet
- Hedera Docs: https://docs.hedera.com
- Polymarket API: ../polymarket-agent/API_DOCUMENTATION.md

---

**Built for ETH Global Buenos Aires 2025** 🇦🇷
