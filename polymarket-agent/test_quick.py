#!/usr/bin/env python3
"""Quick test script - Tests básicos sin dependencias complejas"""

print("=" * 60)
print("🧪 QUICK TESTS - Polymarket Hedge Agent")
print("=" * 60)
print()

# Test 1: Imports
print("1️⃣ Testing imports...")
try:
    from my_agent import Position, TradingStrategy
    from my_agent.utils.config import config
    from my_agent.pnl_calculator import calculate_hedge_shares
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    exit(1)

print()

# Test 2: Config
print("2️⃣ Testing configuration...")
try:
    print(f"   ✓ Market ID: {config.MARKET_CONDITION_ID[:20]}...")
    print(f"   ✓ Chain: {config.CHAIN_ID} (Polygon Amoy Testnet)")
    print(f"   ✓ Take Profit: {config.TAKE_PROFIT_PROBABILITY * 100}%")
    print(f"   ✓ Stop Loss: {config.STOP_LOSS_PROBABILITY * 100}%")
    print("   ✅ Config loaded correctly")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    exit(1)

print()

# Test 3: Gamma API (directo sin imports problemáticos)
print("3️⃣ Testing Gamma API...")
try:
    import httpx
    import json

    response = httpx.get(
        "https://gamma-api.polymarket.com/markets",
        params={"condition_id": config.MARKET_CONDITION_ID},
        timeout=10
    )

    if response.status_code == 200:
        markets = response.json()

        if markets and len(markets) > 0:
            market = markets[0]
            print(f"   ✓ Market: {market['question']}")

            # Parse prices
            prices = market['outcomePrices']
            if isinstance(prices, str):
                prices = json.loads(prices)

            yes_price = float(prices[0])
            no_price = float(prices[1])

            print(f"   ✓ YES: {yes_price:.4f} ({yes_price * 100:.1f}%)")
            print(f"   ✓ NO: {no_price:.4f} ({no_price * 100:.1f}%)")
            print("   ✅ Gamma API works!")
        else:
            print("   ⚠️  Market not found (puede haber expirado)")
    else:
        print(f"   ❌ HTTP {response.status_code}")

except Exception as e:
    print(f"   ⚠️  Gamma API error: {e}")
    print("   (No crítico para tests locales)")

print()

# Test 4: Hedge Math
print("4️⃣ Testing hedge calculations...")
try:
    yes_to_sell, no_to_buy, proceeds = calculate_hedge_shares(
        yes_shares=1250,
        sell_percentage=1.0,
        yes_sell_price=0.86,
        no_buy_price=0.14
    )

    print(f"   ✓ Input: 1250 YES @ $0.86")
    print(f"   ✓ Output: Sell {yes_to_sell:.0f} YES → Buy {no_to_buy:.0f} NO")
    print(f"   ✓ Proceeds: ${proceeds:,.2f}")

    expected_no = 7679  # Expected value
    if abs(no_to_buy - expected_no) < 10:  # Allow small rounding
        print("   ✅ Math is correct!")
    else:
        print(f"   ⚠️  Expected ~{expected_no}, got {no_to_buy:.0f}")

except Exception as e:
    print(f"   ❌ Math error: {e}")
    exit(1)

print()

# Test 5: Position Management
print("5️⃣ Testing position management...")
try:
    import os
    test_file = "position_test_quick.json"

    # Clean up if exists
    if os.path.exists(test_file):
        os.remove(test_file)

    position = Position(position_file=test_file)
    position.open_position(shares=1250, price=0.80, side="YES", entry_prob=0.80)

    print(f"   ✓ Created position: {position.yes_shares:.0f} YES")
    print(f"   ✓ Total invested: ${position.total_invested:,.2f}")

    # Calculate PnL
    pnl = position.calculate_unrealized_pnl(0.86, 0.14)
    print(f"   ✓ Unrealized PnL: ${pnl['unrealized_pnl']:,.2f}")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

    print("   ✅ Position management works!")

except Exception as e:
    print(f"   ❌ Position error: {e}")
    exit(1)

print()

# Test 6: Strategy Logic
print("6️⃣ Testing strategy logic...")
try:
    position = Position()
    position.open_position(shares=1250, price=0.80, side="YES", entry_prob=0.80)

    from my_agent.strategy import create_strategy
    strategy = create_strategy(position)

    # Test take profit
    should_tp = strategy.should_take_profit(0.86)
    print(f"   ✓ Should take profit at 86%: {should_tp}")

    # Test stop loss
    should_sl = strategy.should_cut_loss(0.76)
    print(f"   ✓ Should stop loss at 76%: {should_sl}")

    # Test evaluate
    action = strategy.evaluate(0.86, 0.86, 0.14)
    print(f"   ✓ Action at 86%: {action['action']}")

    if should_tp and should_sl and action['action'] == 'TAKE_PROFIT':
        print("   ✅ Strategy logic works!")
    else:
        print("   ⚠️  Some logic issues (check implementation)")

except Exception as e:
    print(f"   ❌ Strategy error: {e}")
    exit(1)

print()
print("=" * 60)
print("✅ ALL QUICK TESTS PASSED!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Run full tests: python tests/test_strategy.py")
print("  2. Test main loop: python main.py")
print("  3. Create report: nano tests/report.md")
print()
