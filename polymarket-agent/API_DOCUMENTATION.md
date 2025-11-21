# Polymarket Hedge Agent API Documentation

**Base URL:** `http://localhost:5001`

**Purpose:** HTTP API wrapper for Polymarket hedge agent, designed for Hedera A2A integration.

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "polymarket-hedge-agent-api",
  "version": "1.0.0"
}
```

---

### 2. Get Position

**GET** `/position`

Get current trading position status.

**Response:**
```json
{
  "yes_shares": 1250.0,
  "no_shares": 0.0,
  "total_invested": 1000.0,
  "total_withdrawn": 0.0,
  "has_position": true,
  "is_hedged": false,
  "entry_prob": 0.80,
  "avg_cost_yes": 0.80,
  "avg_cost_no": 0.0
}
```

---

### 3. Execute Bet (Main Endpoint)

**POST** `/bet`

Execute trading actions: enter position, evaluate, hedge, or exit.

#### Actions

##### a) **Enter Position**

Opens initial YES position.

**Request:**
```json
{
  "action": "enter",
  "amount_usd": 1000,
  "current_prob": 0.80,
  "yes_price": 0.80
}
```

**Response:**
```json
{
  "success": true,
  "action": "ENTRY",
  "message": "Opened position: 1250.00 YES @ $0.8000",
  "position": {
    "yes_shares": 1250.0,
    "invested": 1000.0
  }
}
```

---

##### b) **Evaluate Position**

Analyzes current market and recommends action.

**Request:**
```json
{
  "action": "evaluate",
  "current_prob": 0.86,
  "yes_price": 0.86,
  "no_price": 0.14
}
```

**Response (Take Profit Recommended):**
```json
{
  "success": true,
  "action": "TAKE_PROFIT",
  "reason": "Probability 86.0% >= 85.0%",
  "current_prob": 0.86,
  "position": {
    "yes_shares": 1250.0,
    "no_shares": 0.0,
    "is_hedged": false
  }
}
```

**Possible Actions:**
- `TAKE_PROFIT` - Should execute hedge
- `STOP_LOSS` - Should exit position
- `HOLD` - Stay in current position
- `WAIT` - No position open

---

##### c) **Execute Hedge**

Executes take-profit hedge strategy.

**Request:**
```json
{
  "action": "hedge",
  "current_prob": 0.86,
  "yes_price": 0.86,
  "no_price": 0.14
}
```

**Response:**
```json
{
  "success": true,
  "action": "HEDGE",
  "locked_pnl_usd": 0.0,
  "message": "Hedge executed: sold 1250 YES, bought 7679 NO",
  "position": {
    "yes_shares": 0.0,
    "no_shares": 7678.57,
    "locked_pnl": 0.0
  },
  "trade_details": {
    "yes_sold": 1250.0,
    "yes_price": 0.86,
    "no_bought": 7678.57,
    "no_price": 0.14,
    "proceeds": 1075.0
  }
}
```

**Error (if conditions not met):**
```json
{
  "success": false,
  "error": "Take-profit not triggered (prob 82.0% < 85.0%)"
}
```

---

##### d) **Exit Position**

Executes stop-loss exit.

**Request:**
```json
{
  "action": "exit",
  "current_prob": 0.75,
  "yes_price": 0.75,
  "no_price": 0.25
}
```

**Response:**
```json
{
  "success": true,
  "action": "STOP_LOSS",
  "final_pnl_usd": -250.0,
  "message": "Position exited: $937.50 recovered",
  "trade_details": {
    "yes_sold": 1250.0,
    "no_sold": 0.0,
    "total_proceeds": 937.5
  }
}
```

---

### 4. Reset Position

**POST** `/reset`

Reset position to empty (for testing).

**Response:**
```json
{
  "success": true,
  "message": "Position reset successfully"
}
```

---

## Complete Trading Flow Example

### Scenario: Enter → Evaluate → Hedge

```bash
# 1. Enter position at 80% probability
curl -X POST http://localhost:5001/bet \
  -H "Content-Type: application/json" \
  -d '{"action":"enter","amount_usd":1000,"current_prob":0.80,"yes_price":0.80}'

# Response: Bought 1250 YES @ $0.80 = $1000 invested

# 2. Price rises to 86% - evaluate
curl -X POST http://localhost:5001/bet \
  -H "Content-Type: application/json" \
  -d '{"action":"evaluate","current_prob":0.86,"yes_price":0.86,"no_price":0.14}'

# Response: TAKE_PROFIT recommended (86% >= 85% threshold)

# 3. Execute hedge
curl -X POST http://localhost:5001/bet \
  -H "Content-Type: application/json" \
  -d '{"action":"hedge","current_prob":0.86,"yes_price":0.86,"no_price":0.14}'

# Response: Sold 1250 YES @ $0.86 = $1075
#           Bought 7679 NO @ $0.14 = $1075
#           Locked profit: $75 (if YES wins) or $6,679 (if NO wins)
```

---

## Strategy Thresholds

- **Take Profit:** 85% (configurable via `TAKE_PROFIT_PROBABILITY` in `.env`)
- **Stop Loss:** 78% (configurable via `STOP_LOSS_PROBABILITY` in `.env`)
- **Hedge Percentage:** 100% of YES shares (configurable via `HEDGE_SELL_PERCENT`)

---

## Error Handling

All errors return:
```json
{
  "success": false,
  "error": "Error message",
  "traceback": "..." // Only in debug mode
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad request (invalid action, conditions not met)
- `500` - Server error

---

## Integration with Hedera A2A

### Recommended Flow

1. **Hedera Agent** sends A2A message with bet proposal
2. **Polymarket Agent** calls `/bet` with `action: "evaluate"`
3. If `TAKE_PROFIT` recommended:
   - Call `/bet` with `action: "hedge"`
   - Return locked PnL in A2A response
4. **Hedera Agent** settles payment via HTS based on result

### Example Hedera Integration

```javascript
// Hedera agent calls Polymarket API
const response = await fetch('http://localhost:5001/bet', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'evaluate',
    current_prob: 0.86,
    yes_price: 0.86,
    no_price: 0.14
  })
});

const result = await response.json();

if (result.action === 'TAKE_PROFIT') {
  // Execute hedge
  const hedgeResponse = await fetch('http://localhost:5001/bet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'hedge',
      current_prob: 0.86,
      yes_price: 0.86,
      no_price: 0.14
    })
  });

  const hedgeResult = await hedgeResponse.json();
  console.log(`Locked PnL: $${hedgeResult.locked_pnl_usd}`);

  // Settle on Hedera
  await settleOnHedera(hedgeResult.locked_pnl_usd);
}
```

---

## Running the API

```bash
# Install dependencies
pip install flask flask-cors

# Start server
python3 api.py

# Server runs on http://localhost:5001
```

---

## Notes

- **No Blockchain Execution:** API never executes real blockchain transactions (safety feature)
- **Demo Mode:** All trades are simulated and tracked in `position_api.json`
- **Port 5001:** Changed from 5000 to avoid conflict with macOS AirPlay
- **CORS Enabled:** Frontend can call from different origin

---

**For Hackathon:** This API enables cross-chain agent communication where Hedera agents can negotiate bets and Polymarket agent executes the hedging strategy.
