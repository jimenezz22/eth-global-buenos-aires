# API Usage

## Overview

The agent integrates with three APIs:
1. **Polymarket Gamma API** - Market data retrieval
2. **Polymarket CLOB API** - Trade execution
3. **Google Gemini API** - AI analysis

---

## 1. Polymarket Gamma API

**Purpose:** Fetch real-time market probabilities

**Endpoint:**
```
GET https://gamma-api.polymarket.com/markets
```

**Implementation:**
```python
# File: main.py:147-189

markets = gamma_client.get_markets(
    {"condition_ids": condition_id},
    parse_pydantic=False
)

market = markets[0]
prices = json.loads(market['outcomePrices'])
yes_price = float(prices[0])  # 0.85 = 85% probability
no_price = float(prices[1])   # 0.15 = 15% probability
```

**Rate Limit:** None observed
**Response Time:** ~500ms average
**Usage:** Polled every 20 seconds in main loop

---

## 2. Polymarket CLOB API

**Purpose:** Execute trades on Polygon blockchain

**Authentication:** EIP-712 signed orders with wallet private key

**Implementation:**
```python
# File: position.py:100-107

order_result = self.polymarket_client.execute_order(
    price=price,        # e.g. 0.85
    size=shares,        # e.g. 1250
    side="BUY",         # or "SELL"
    token_id=token_id   # market identifier
)
# Returns: Order ID or transaction hash
```

**Under the hood:**
```python
# Official SDK: agents/polymarket/polymarket.py:336-339

def execute_order(self, price, size, side, token_id):
    return self.client.create_and_post_order(
        OrderArgs(price, size, side, token_id)
    )
    # 1. Signs order with private key (EIP-712)
    # 2. Posts to Polymarket CLOB
    # 3. CLOB matches order on-chain
    # 4. USDC transferred, shares minted/burned
```

**Network:** Polygon Mainnet (Chain ID: 137)
**Token:** USDC (0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174)

---

## 3. Google Gemini API 

**Purpose:** AI-enhanced trading decisions

**Model:** gemini-2.5-flash (free tier)

**Implementation:**
```python
# File: ai_advisor.py:128-148

response = gemini_model.generate_content(f"""
You are a trading advisor for Polymarket.

Market: {market_question}
Current Probability: {current_prob * 100:.1f}%
Position: {position_summary}
Rule-Based Decision: {rule_based_action}

Should I follow the rule or override? Provide:
1. CONFIRM or OVERRIDE_[ACTION]
2. Confidence (0-100)
3. Reasoning
""")

# Parse response
if "CONFIRM" in response.text:
    action = rule_based_action
elif "OVERRIDE_HOLD" in response.text:
    action = "HOLD"
```

**Cost:** Free
**Response Time:** ~1-2s
**Usage:** Called on each strategy evaluation (optional)

---

## Error Handling

### API Failures
```python
# File: helpers.py:60-98

def retry_with_backoff(func, max_retries=3):
    delay = 1.0
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)
            delay *= 2.0
```

### Transaction Failures
```python
# File: position.py:108-111

try:
    order_result = self.polymarket_client.execute_order(...)
    log_success(f"✅ Order executed: {order_result}")
except Exception as e:
    log_warning(f"❌ Transaction failed: {e}")
    raise
```

---

## Configuration

**File:** `.env`
```bash
# Polymarket
POLYGON_WALLET_PRIVATE_KEY=0x...
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/xxx
MARKET_CONDITION_ID=0x9c8f9e...

# AI (Optional)
GOOGLE_API_KEY=AIzaSy...

# Network
CHAIN_ID=137
```

**File:** `my_agent/utils/config.py`
```python
class Config:
    PRIVATE_KEY = os.getenv("POLYGON_WALLET_PRIVATE_KEY")
    POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")
    MARKET_CONDITION_ID = os.getenv("MARKET_CONDITION_ID")
    # ... thresholds, intervals, etc.
```

---

## API Keys Setup

1. **Polymarket Wallet:**
   - Create wallet on Polygon
   - Fund with USDC for trading
   - Export private key (never share!)

2. **Google Gemini API:**
   - Visit https://makersuite.google.com/app/apikey
   - Create new API key
   - Free tier: 60 requests/minute

3. **Polygon RPC:**
   - Alchemy: https://www.alchemy.com/
   - Infura: https://infura.io/
   - Or use public RPC (slower)

---

## Testing API Integration

```bash
# Quick API test
python test_quick.py

# Expected output:
# 3️⃣ Testing Gamma API...
#    ✓ Market: [market name]
#    ✓ YES: 0.XXXX (XX.X%)
#    ✓ NO: 0.XXXX (XX.X%)
#    ✅ Gamma API works!
```

---

## References

- **Polymarket Docs:** https://docs.polymarket.com
- **Gamma API:** https://gamma-api.polymarket.com/docs
- **CLOB Client:** https://github.com/Polymarket/py-clob-client
- **Gemini API:** https://ai.google.dev/docs
