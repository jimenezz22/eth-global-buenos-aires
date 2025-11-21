# Architecture

## System Overview

Built on [Polymarket/agents](https://github.com/Polymarket/agents) SDK with custom hedging strategy.

```
┌──────────────────────────────────────┐
│  Main Loop (main.py)                 │
│  • Poll market every 20s             │
│  • Evaluate strategy                 │
│  • Execute trades                    │
└────────┬────────────────┬────────────┘
         │                │
    ┌────▼─────┐     ┌────▼──────┐
    │ Polymarket│     │  Custom   │
    │   SDK     │     │ Strategy  │
    │           │     │           │
    │ • Gamma   │◄───►│ • Hedge   │
    │   API     │     │   Logic   │
    │ • CLOB    │     │ • P&L     │
    │   Client  │     │   Calc    │
    │ • Wallet  │     │ • AI      │
    └───────────┘     └───────────┘
```

---

## Core Components

### 1. Main Loop
**File:** `main.py`
**Purpose:** Orchestration

```python
while not killer.kill_now:
    # 1. Fetch market data
    markets = gamma_client.get_markets(condition_id)
    yes_price, no_price = parse_prices(markets)

    # 2. Evaluate strategy
    action = strategy.evaluate(yes_price, no_price)

    # 3. Execute if needed
    if action["action"] in ["TAKE_PROFIT", "STOP_LOSS"]:
        strategy.execute_action(action)

    # 4. Wait
    time.sleep(POLL_INTERVAL)
```

---

### 2. Trading Strategy
**File:** `my_agent/strategy.py` (311 lines)
**Purpose:** Decision logic

**Key Methods:**
```python
class TradingStrategy:
    def should_take_profit(prob) -> bool:
        """Check if prob >= 85%"""

    def should_cut_loss(prob) -> bool:
        """Check if prob <= 78%"""

    def book_profit_and_rebalance(yes_price, no_price):
        """Sell YES → Buy NO"""

    def cut_loss_and_exit(yes_price, no_price):
        """Sell all positions"""
```

---

### 3. Position Manager
**File:** `my_agent/position.py` (347 lines)
**Purpose:** State tracking + trade execution

**Responsibilities:**
- Track YES/NO shares
- Calculate P&L
- Execute blockchain transactions
- Persist state to `position.json`

**Key Methods:**
```python
class Position:
    def open_position(shares, price, side):
        """Buy shares"""

    def sell_shares(shares, price, side):
        """Sell shares"""

    def calculate_unrealized_pnl(yes_price, no_price):
        """Current position value"""

    def calculate_locked_pnl():
        """Guaranteed profit from hedge"""
```

---

### 4. PnL Calculator
**File:** `my_agent/pnl_calculator.py` (53 lines)
**Purpose:** Hedge math

**Formula:**
```python
def calculate_hedge_shares(yes_shares, yes_price, no_price, sell_pct):
    yes_to_sell = yes_shares * sell_pct
    usdc_proceeds = yes_to_sell * yes_price
    no_to_buy = usdc_proceeds / no_price
    return (yes_to_sell, no_to_buy, usdc_proceeds)
```

---

### 5. AI Advisor
**File:** `my_agent/ai_advisor.py` (346 lines)
**Purpose:** Enhance decisions with LLM

**Providers:**
- Google Gemini (free)
- OpenAI GPT
- Anthropic Claude

**Workflow:**
```python
rule_decision = strategy.evaluate(...)
ai_analysis = ai_advisor.analyze_market_sentiment(...)

if ai_analysis["recommendation"] == "OVERRIDE_HOLD":
    final_decision = "HOLD"  # AI overrides
else:
    final_decision = rule_decision  # Follow rules
```

---

## Data Flow

```
1. Gamma API → Market Data
   ↓
2. Strategy → Evaluate
   ↓
3. AI Advisor → Analyze
   ↓
4. Position → Execute Trade
   ↓
5. Polymarket CLOB → Blockchain
   ↓
6. position.json → Save State
```

---

## File Structure

```
polymarket-agent/
├── main.py                    # Entry point (386 lines)
├── my_agent/                  # Custom logic
│   ├── strategy.py            # Trading strategy (311 lines)
│   ├── position.py            # Position tracking (347 lines)
│   ├── pnl_calculator.py      # Hedge math (53 lines)
│   ├── ai_advisor.py          # AI integration (346 lines)
│   └── utils/
│       ├── config.py          # Configuration (249 lines)
│       ├── constants.py       # Constants (180 lines)
│       ├── logger.py          # Logging (159 lines)
│       └── helpers.py         # Utilities (369 lines)
├── agents/                    # Polymarket SDK
│   └── polymarket/
│       ├── polymarket.py      # Client (500+ lines)
│       └── gamma.py           # Market data
├── tests/                     # Tests
│   ├── test_strategy.py
│   ├── test_position.py
│   └── test_pnl.py
└── position.json              # State file (generated)
```

**Total:** ~2,500 lines of custom code

---

## Configuration

**File:** `.env`
```bash
# Required
POLYGON_WALLET_PRIVATE_KEY=0x...
MARKET_CONDITION_ID=0x...

# Optional
GOOGLE_API_KEY=AIzaSy...
DEMO_MODE=true

# Thresholds
TAKE_PROFIT_PROBABILITY=0.85
STOP_LOSS_PROBABILITY=0.78
HEDGE_SELL_PERCENT=1.0
POLL_INTERVAL_SECONDS=20
```

**File:** `position.json` (auto-generated)
```json
{
  "yes_shares": 1250.0,
  "no_shares": 0.0,
  "total_invested": 1000.0,
  "total_withdrawn": 0.0,
  "avg_cost_yes": 0.80,
  "avg_cost_no": 0.0,
  "entry_timestamp": "2025-11-19T10:30:00",
  "entry_prob": 0.80,
  "trades": [...]
}
```

---

## Dependencies

**Core:**
- `py-clob-client` - Polymarket official client
- `web3` - Ethereum/Polygon transactions
- `python-dotenv` - Environment variables

**AI (Optional):**
- `google-generativeai` - Gemini API
- `langchain` - LLM framework

**Utils:**
- `rich` - CLI formatting
- `pytest` - Testing

**See:** `requirements.txt` for full list

---

## Design Patterns

### 1. Strategy Pattern
```python
# Different strategies can be plugged in
strategy = TradingStrategy(position, thresholds)
strategy = ArbitrageStrategy(position)  # Future
strategy = MarketMakingStrategy(position)  # Future
```

### 2. Singleton
```python
# One Position instance per market
position = Position.get_instance(market_id)
```

### 3. Observer (Implicit)
```python
# Main loop observes market changes
while True:
    market_data = fetch_market()
    strategy.on_price_change(market_data)
```

---

## Scalability Considerations

**Current (MVP):**
- Single market
- Synchronous execution
- JSON storage
- 20s polling

**Future (See FUTURE.md):**
- Multi-market portfolio
- Async/WebSocket
- Database backend
- <1s latency

---

## Security Architecture

**Layers:**
1. **Private key** - Stored in `.env`, never logged
2. **EIP-712** - Signed orders (industry standard)
3. **Demo mode** - Test without real funds
4. **Error handling** - Transaction rollback on failure

**See:** [SECURITY.md](SECURITY.md) for details

---

## Testing Strategy

**Unit Tests:**
- Strategy logic
- PnL calculations
- Position updates

**Integration Tests:**
- API connectivity
- Trade execution flow
- State persistence

**Run:** `python test_quick.py` (6 tests, ~3s)

---

## Performance

```
Poll Interval: 20s
API Latency: ~500ms (Gamma)
AI Latency: ~1-2s (Gemini, optional)
Memory: ~80MB
CPU: <5% idle, ~15% active
```

---

## References

- **Polymarket Agents:** https://github.com/Polymarket/agents
- **CLOB Client:** https://github.com/Polymarket/py-clob-client
- **Gamma API Docs:** https://gamma-api.polymarket.com/docs
