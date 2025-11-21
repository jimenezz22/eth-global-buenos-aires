# Security & Wallet Integration

## Overview

The agent executes real blockchain transactions on Polygon using:
- **Web3.py** for wallet management
- **EIP-712** for transaction signing
- **Polymarket SDK** for order execution

---

## Wallet Setup

### 1. Create Polygon Wallet

```bash
# Using MetaMask or any Web3 wallet
# Network: Polygon Mainnet
# Chain ID: 137
```

### 2. Export Private Key

```
MetaMask → Account Details → Export Private Key
⚠️ NEVER share this key!
```

### 3. Fund Wallet

```
Required:
- MATIC (for gas fees) ~$5
- USDC (for trading) $100+

Bridge: https://wallet.polygon.technology/bridge
```

---

## Configuration

### Environment Variables

**File:** `.env`
```bash
# Private key (WITH 0x prefix)
POLYGON_WALLET_PRIVATE_KEY=0x1234567890abcdef...

# RPC endpoint
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/xxx

# Network
CHAIN_ID=137
```

**⚠️ Security:**
- `.env` is in `.gitignore` (never committed)
- Use `.env.example` for templates only

### Loading Credentials

**File:** `my_agent/utils/config.py:14-20`
```python
from dotenv import load_dotenv
load_dotenv()

class Config:
    PRIVATE_KEY = os.getenv("POLYGON_WALLET_PRIVATE_KEY")

    @classmethod
    def validate(cls):
        if not cls.PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY required")

        # Ensure 0x prefix
        if not cls.PRIVATE_KEY.startswith("0x"):
            cls.PRIVATE_KEY = f"0x{cls.PRIVATE_KEY}"
```

---

## Transaction Signing

### EIP-712 Typed Data Signing

**What it is:** Ethereum standard for structured, human-readable signatures

**File:** `agents/polymarket/polymarket.py:336-339`
```python
def execute_order(self, price, size, side, token_id):
    """Execute order with EIP-712 signature."""
    return self.client.create_and_post_order(
        OrderArgs(
            price=price,
            size=size,
            side=side,  # "BUY" or "SELL"
            token_id=token_id
        )
    )
```

### Under the Hood

```python
# Polymarket SDK handles:

# 1. Create order struct
order = {
    "maker": wallet_address,
    "price": price,
    "size": size,
    "side": side,
    "token_id": token_id,
    "nonce": get_nonce()
}

# 2. Sign with private key (EIP-712)
signature = web3.eth.account.sign_typed_data(
    private_key=PRIVATE_KEY,
    domain=POLYMARKET_DOMAIN,
    message_types=ORDER_TYPES,
    message=order
)

# 3. Submit to CLOB
response = requests.post(
    "https://clob.polymarket.com/order",
    json={"order": order, "signature": signature}
)
```

---

## Trade Execution Flow

### 1. Position Opening

**File:** `my_agent/position.py:94-113`
```python
def open_position(shares, price, side, execute_trade=False):
    """Buy shares (YES or NO)."""

    if execute_trade and self.polymarket_client:
        # Real blockchain transaction
        order_result = self.polymarket_client.execute_order(
            price=price,
            size=shares,
            side="BUY",
            token_id=self.token_id
        )
        log_success(f"✅ Order: {order_result}")
    else:
        # Demo mode
        log_info(f"📝 DEMO: Simulating BUY")

    # Update local state
    self.yes_shares += shares
    self.total_invested += (shares * price)
    self.save()
```

### 2. Position Closing

**File:** `my_agent/position.py:177-198`
```python
def sell_shares(shares, price, side, execute_trade=False):
    """Sell shares (YES or NO)."""

    if execute_trade and self.polymarket_client:
        # Real blockchain transaction
        order_result = self.polymarket_client.execute_order(
            price=price,
            size=shares,
            side="SELL",
            token_id=self.token_id
        )
        log_success(f"✅ Sold: {order_result}")
    else:
        # Demo mode
        log_info(f"📝 DEMO: Simulating SELL")

    # Update local state
    self.yes_shares -= shares
    self.total_withdrawn += (shares * price)
    self.save()
```

---

## USDC Approval (One-Time)

Before trading, approve Polymarket exchange to spend USDC:

**File:** `agents/polymarket/polymarket.py:92-105`
```python
# Approve USDC spending
usdc_contract = web3.eth.contract(
    address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    abi=ERC20_ABI
)

# Approve max amount
tx = usdc_contract.functions.approve(
    "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",  # Exchange
    int("0xffffffffffffffffffffffffffffffff", 16)   # Max uint256
).build_transaction({
    "from": wallet_address,
    "nonce": nonce,
    "chainId": 137
})

# Sign and send
signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
```

**Run once:** `python agents/application/approve_usdc.py`

---

## Demo Mode (Safe Testing)

### Configuration

**File:** `.env`
```bash
DEMO_MODE=true  # Default: enabled
```

**File:** `my_agent/utils/config.py:90-92`
```python
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
```

### Behavior

```python
if config.DEMO_MODE:
    # Simulates trades locally
    # Updates position.json
    # NO blockchain transactions
    # NO real money spent
else:
    # Real blockchain transactions
    # Requires USDC + MATIC
    # Actual trades executed
```

**⚠️ Always test in demo mode first!**

---

## Error Handling

### Transaction Failures

**File:** `my_agent/position.py:108-111`
```python
try:
    order_result = polymarket_client.execute_order(...)
except Exception as e:
    log_warning(f"❌ Transaction failed: {e}")
    # State NOT updated (transaction rolled back)
    raise
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Insufficient funds` | Not enough USDC | Add USDC to wallet |
| `Gas estimation failed` | Not enough MATIC | Add MATIC for gas |
| `Order rejected` | Invalid price/size | Check market liquidity |
| `Nonce too low` | Transaction conflict | Wait and retry |

---

## Security Best Practices

### ✅ DO
- Store private key in `.env` file
- Add `.env` to `.gitignore`
- Use hardware wallet for large amounts
- Test in demo mode first
- Keep small amounts in hot wallet
- Monitor transactions on Polygonscan

### ❌ DON'T
- Hardcode private keys in code
- Commit `.env` to git
- Share private keys
- Skip USDC approval step
- Trade without testing
- Ignore transaction errors

---

## Monitoring Transactions

### Polygonscan

```
https://polygonscan.com/address/YOUR_WALLET_ADDRESS
```

### Check Balance

```python
# In Python console
from web3 import Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# ETH (MATIC) balance
balance_wei = web3.eth.get_balance(wallet_address)
balance_matic = web3.from_wei(balance_wei, 'ether')
print(f"MATIC: {balance_matic}")

# USDC balance
usdc = web3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
balance = usdc.functions.balanceOf(wallet_address).call()
balance_usdc = balance / 10**6  # USDC has 6 decimals
print(f"USDC: {balance_usdc}")
```

---

## Testing Security

```bash
# 1. Verify configuration
python test_quick.py

# Expected output:
# 2️⃣ Testing configuration...
#    ✓ Private Key: 0x7Ae7...A931 (masked)
#    ✓ Chain: 137 (Polygon Mainnet)
#    ✅ Config loaded correctly

# 2. Test in demo mode
DEMO_MODE=true python main.py

# 3. Test real transaction (small amount!)
DEMO_MODE=false python main.py
```

---

## Contracts Used

```
Polygon Mainnet (Chain ID: 137)

USDC:
0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174

Polymarket Exchange:
0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E

CTF (Conditional Token Framework):
0x4D97DCd97eC945f40cF65F87097ACe5EA0476045
```

---

## References

- **Web3.py Docs:** https://web3py.readthedocs.io/
- **EIP-712:** https://eips.ethereum.org/EIPS/eip-712
- **Polymarket Contracts:** https://docs.polymarket.com/#contracts
- **Polygon:** https://docs.polygon.technology/
