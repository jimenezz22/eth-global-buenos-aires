# Trading Logic

## Strategy Overview

The agent uses a **profit-locking hedging strategy** with two triggers:
1. **Take Profit** (≥85% probability) - Hedge position to lock gains
2. **Stop Loss** (≤78% probability) - Exit position to limit losses

---

## Decision Flow

```
Market Probability Check
         │
    ┌────▼────┐
    │  ≥85%?  │ YES → TAKE_PROFIT (hedge)
    └────┬────┘
         │ NO
    ┌────▼────┐
    │  ≤78%?  │ YES → STOP_LOSS (exit)
    └────┬────┘
         │ NO
    ┌────▼────┐
    │  HOLD   │ → Continue monitoring
    └─────────┘
```

**Implementation:** `my_agent/strategy.py:226-275`

---

## Take Profit & Hedge

### Trigger Condition
```python
if current_prob >= 0.85:  # 85%
    execute_take_profit()
```

### Execution Steps

**File:** `strategy.py:80-150`

```python
def book_profit_and_rebalance(yes_price, no_price):
    # 1. Calculate hedge
    yes_to_sell = position.yes_shares * HEDGE_SELL_PERCENT  # e.g. 100%
    usdc_proceeds = yes_to_sell * yes_price
    no_to_buy = usdc_proceeds / no_price

    # 2. Execute trades
    position.sell_shares(yes_to_sell, yes_price, side="YES")
    position.open_position(no_to_buy, no_price, side="NO")

    # 3. Result: Hedged position
    return {
        "yes_sold": yes_to_sell,
        "no_bought": no_to_buy,
        "locked_pnl": calculate_locked_pnl()
    }
```

### Example: Bitcoin Below 90k

**Initial Position:**
```
Entry: 1,250 YES @ $0.80 = $1,000 invested
```

**Market moves to 85%:**
```
Take Profit Triggered!

Step 1: Sell YES
  1,250 YES × $0.85 = $1,062.50 proceeds

Step 2: Buy NO with proceeds
  $1,062.50 ÷ $0.15 = 7,083 NO shares

New Position:
  YES: 0 shares
  NO: 7,083 shares
```

**Outcome Analysis:**
```
If YES wins (price → $1.00):
  Payout: 0 × $1.00 = $0

If NO wins (price → $1.00):
  Payout: 7,083 × $1.00 = $7,083

Cost Basis:
  Initial: $1,000 (YES purchase)
  Rebalance: $1,062.50 (sold) - $1,062.50 (bought) = $0 net
  Total Cost: $1,000

Profit if NO wins: $7,083 - $1,000 = $6,083 ✅
Loss if YES wins: $0 - $1,000 = -$1,000 ❌
```

**Key Insight:** If probability rose from 80% → 85%, the market believes NO is more likely. By hedging, we lock in profit if that prediction holds.

---

## Stop Loss & Exit

### Trigger Condition
```python
if current_prob <= 0.78:  # 78%
    execute_stop_loss()
```

### Execution Steps

**File:** `strategy.py:152-224`

```python
def cut_loss_and_exit(yes_price, no_price):
    # 1. Sell all positions
    total_proceeds = 0

    if position.yes_shares > 0:
        proceeds = position.sell_shares(
            position.yes_shares,
            yes_price,
            side="YES"
        )
        total_proceeds += proceeds

    if position.no_shares > 0:
        proceeds = position.sell_shares(
            position.no_shares,
            no_price,
            side="NO"
        )
        total_proceeds += proceeds

    # 2. Calculate final P&L
    final_pnl = total_proceeds - position.total_invested

    # 3. Reset position
    position.reset()

    return {"final_pnl": final_pnl}
```

### Example: Bitcoin Below 90k

**Initial Position:**
```
Entry: 1,250 YES @ $0.80 = $1,000 invested
```

**Market drops to 76%:**
```
Stop Loss Triggered!

Step 1: Sell all YES
  1,250 YES × $0.76 = $950

Final P&L:
  Proceeds: $950
  Invested: $1,000
  Loss: -$50 (-5%) ❌

Position: CLOSED
```

**Key Insight:** Market moved against us (80% → 76%). Exit now to minimize loss rather than holding to $0.

---

## Hedge Math Explained

### Why Hedging Works

When probability rises (80% → 85%):
- YES price increases ($0.80 → $0.85)
- NO price decreases ($0.20 → $0.15)

By selling expensive YES and buying cheap NO:
- Lock in the price difference as profit
- Guarantee payout from one side

### Calculation Formula

**File:** `pnl_calculator.py:6-33`

```python
def calculate_hedge_shares(
    yes_shares: float,
    yes_sell_price: float,
    no_buy_price: float,
    sell_percentage: float = 1.0
) -> tuple:
    """
    Calculate hedge rebalancing.

    Returns:
        (yes_to_sell, no_to_buy, usdc_proceeds)
    """
    yes_to_sell = yes_shares * sell_percentage
    usdc_proceeds = yes_to_sell * yes_sell_price
    no_to_buy = usdc_proceeds / no_buy_price

    return (yes_to_sell, no_to_buy, usdc_proceeds)
```

### Partial Hedge

```python
# Sell only 60% of YES, keep 40%
HEDGE_SELL_PERCENT = 0.6

# Example:
1,250 YES × 60% = 750 YES sold
500 YES remain

# Result: Hedged + upside exposure
```

---

## AI-Enhanced Decisions 

**File:** `ai_advisor.py:91-158`

The AI can override rule-based decisions:

```python
# Example override
Rule: STOP_LOSS (76% < 78%)
AI Analysis: "Buffalo Bills are playoff contenders,
              76% still reasonable given recent wins"
AI Decision: OVERRIDE → HOLD
Final Action: HOLD (trust AI)
```

**When to use:**
- Market has external context (news, events)
- Probability near threshold (77%-79%, 84%-86%)
- Confidence score > 70%

---

## Configuration

**File:** `.env`
```bash
# Thresholds
TAKE_PROFIT_PROBABILITY=0.85  # 85%
STOP_LOSS_PROBABILITY=0.78    # 78%
HEDGE_SELL_PERCENT=1.0         # 100% hedge (recommended)

# Timing
POLL_INTERVAL_SECONDS=20       # Check every 20s
```

**Recommended Settings:**
- **Conservative:** TP=0.90, SL=0.75 (wider spread)
- **Aggressive:** TP=0.83, SL=0.80 (narrow spread)
- **Balanced:** TP=0.85, SL=0.78 (default)

---

## Risk Management

### Position Size
```python
# Never risk more than you can afford to lose
INITIAL_INVESTMENT = 1000  # USDC
MAX_POSITION_SIZE = 0.1 * portfolio_value  # 10% max
```

### Slippage Protection
```python
# Ensure price hasn't moved too much
if abs(current_price - expected_price) > MAX_SLIPPAGE:
    abort_trade()
```

**File:** `config.py:37-38`

---

## Testing Strategy Logic

```bash
# Run strategy tests
python test_quick.py

# Test scenarios:
# ✅ Scenario 1: Take Profit (80% → 86%)
# ✅ Scenario 2: Stop Loss (80% → 76%)
# ✅ Scenario 3: Hedge Protection (85% → 50% crash)
```

**File:** `test_quick.py:18-264`

---

## References

- **Strategy Code:** `my_agent/strategy.py`
- **Hedge Math:** `my_agent/pnl_calculator.py`
- **Tests:** `test_quick.py`
