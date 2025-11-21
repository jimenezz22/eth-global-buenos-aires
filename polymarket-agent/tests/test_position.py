#!/usr/bin/env python3
"""Test script for Phase 2 - Position Manager & PnL Calculator."""

import os
from my_agent.utils.logger import (
    console,
    log_info,
    log_success,
    log_error,
    print_header,
    print_status_table
)
from my_agent.position import Position, get_position
from my_agent.pnl_calculator import (
    calculate_hedge_shares,
    calculate_final_pnl_scenarios,
    calculate_roi,
    format_pnl,
    format_roi
)


def test_position_creation():
    """Test creating a new position."""
    print_header("Position Creation Test")

    # Clean up any existing test file
    test_file = "position_test.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        # Create position
        position = Position(position_file=test_file)

        # Open initial position: Buy 1250 YES shares at $0.80
        position.open_position(
            shares=1250.0,
            price=0.80,
            side="YES",
            entry_prob=0.80
        )

        log_success(f"Position created with {position.yes_shares} YES shares")
        print_status_table({
            "YES Shares": position.yes_shares,
            "Avg Cost": f"${position.avg_cost_yes:.4f}",
            "Total Invested": f"${position.total_invested:,.2f}",
            "Entry Prob": f"{position.entry_prob * 100:.1f}%"
        })

        return True

    except Exception as e:
        log_error(f"Position creation failed: {e}")
        return False


def test_pnl_calculations():
    """Test PnL calculations."""
    print_header("PnL Calculation Test")

    test_file = "position_test.json"

    try:
        position = Position(position_file=test_file)

        # Current price: 0.86 (prob increased)
        yes_price = 0.86
        no_price = 0.14

        # Calculate unrealized PnL
        pnl = position.calculate_unrealized_pnl(yes_price, no_price)

        log_info(f"Current YES price: ${yes_price:.4f} (86%)")
        print_status_table({
            "Current Value": f"${pnl['total_value']:,.2f}",
            "Cost Basis": f"${pnl['total_cost']:,.2f}",
            "Unrealized PnL": format_pnl(pnl['unrealized_pnl']),
            "ROI": format_roi(pnl['roi'])
        })

        if pnl['unrealized_pnl'] > 0:
            log_success(f"Position is profitable: {format_pnl(pnl['unrealized_pnl'])}")
        else:
            log_error(f"Position is losing: {format_pnl(pnl['unrealized_pnl'])}")

        return True

    except Exception as e:
        log_error(f"PnL calculation failed: {e}")
        return False


def test_hedging_simulation():
    """Test hedging scenario."""
    print_header("Hedging Simulation Test")

    test_file = "position_test.json"

    try:
        position = Position(position_file=test_file)

        # Scenario: Prob rose to 86%, trigger take-profit
        yes_price = 0.86
        no_price = 0.14

        log_info("Scenario: Probability rose to 86% → Take Profit + Hedge")

        # Calculate hedge
        sell_pct = 1.0  # Sell 100% of YES
        yes_to_sell, no_to_buy, proceeds = calculate_hedge_shares(
            yes_shares=position.yes_shares,
            sell_percentage=sell_pct,
            yes_sell_price=yes_price,
            no_buy_price=no_price
        )

        console.print()
        log_info(f"Step 1: Sell {yes_to_sell:.0f} YES shares @ ${yes_price:.4f}")
        log_info(f"  → Proceeds: ${proceeds:,.2f}")

        # Execute sell
        position.sell_shares(yes_to_sell, yes_price, side="YES")

        console.print()
        log_info(f"Step 2: Buy {no_to_buy:.0f} NO shares @ ${no_price:.4f}")

        # Execute buy
        position.open_position(no_to_buy, no_price, side="NO")

        console.print()
        log_success("Hedging complete!")
        print_status_table({
            "YES Shares": f"{position.yes_shares:.0f}",
            "NO Shares": f"{position.no_shares:.0f}",
            "Total Invested": f"${position.total_invested:,.2f}",
            "Total Withdrawn": f"${position.total_withdrawn:,.2f}"
        })

        # Calculate locked PnL
        locked_pnl = position.calculate_locked_pnl()

        console.print()
        log_success(f"Locked PnL: {format_pnl(locked_pnl)}")

        # Show outcome scenarios
        total_cost = (position.yes_shares * position.avg_cost_yes) + \
                     (position.no_shares * position.avg_cost_no)

        scenarios = calculate_final_pnl_scenarios(
            yes_shares=position.yes_shares,
            no_shares=position.no_shares,
            total_cost=total_cost
        )

        console.print()
        log_info("Final Outcome Scenarios:")
        print_status_table({
            "If YES wins": format_pnl(scenarios['pnl_if_yes_wins']),
            "If NO wins": format_pnl(scenarios['pnl_if_no_wins']),
            "Guaranteed Min": format_pnl(scenarios['guaranteed_min']),
            "Is Profitable": "✓ Yes" if scenarios['is_profitable'] else "✗ No"
        })

        return True

    except Exception as e:
        log_error(f"Hedging simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stop_loss_simulation():
    """Test stop-loss scenario."""
    print_header("Stop Loss Simulation Test")

    test_file = "position_stoploss_test.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        position = Position(position_file=test_file)

        # Open position at 80%
        position.open_position(1250.0, 0.80, side="YES", entry_prob=0.80)
        log_info(f"Opened position: {position.yes_shares} YES @ $0.80")

        console.print()

        # Scenario: Prob drops to 76% → Stop loss
        stop_loss_price = 0.76
        log_info(f"Scenario: Probability dropped to {stop_loss_price * 100}% → Stop Loss")

        # Sell all YES
        proceeds = position.sell_shares(position.yes_shares, stop_loss_price, side="YES")

        console.print()
        log_info(f"Sold all {1250} YES shares @ ${stop_loss_price:.4f}")
        log_info(f"  → Proceeds: ${proceeds:,.2f}")

        # Calculate final PnL
        pnl = position.total_withdrawn - position.total_invested
        roi = (pnl / position.total_invested * 100) if position.total_invested > 0 else 0

        console.print()
        print_status_table({
            "Total Invested": f"${position.total_invested:,.2f}",
            "Total Withdrawn": f"${position.total_withdrawn:,.2f}",
            "Final PnL": format_pnl(pnl),
            "ROI": format_roi(roi)
        })

        if pnl < 0:
            log_error(f"Loss taken: {format_pnl(pnl)} (better than holding)")
        else:
            log_success(f"Profit: {format_pnl(pnl)}")

        return True

    except Exception as e:
        log_error(f"Stop loss simulation failed: {e}")
        return False


def test_persistence():
    """Test position persistence."""
    print_header("Position Persistence Test")

    test_file = "position_persist_test.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        # Create and save
        pos1 = Position(position_file=test_file)
        pos1.open_position(1000.0, 0.80, side="YES")
        initial_invested = pos1.total_invested

        log_success(f"Created position and saved to {test_file}")

        # Load in new instance
        pos2 = Position(position_file=test_file)

        log_success(f"Loaded position from {test_file}")

        # Verify
        if pos2.yes_shares == 1000.0 and pos2.total_invested == initial_invested:
            log_success("Position data persisted correctly")
            print_status_table({
                "YES Shares": pos2.yes_shares,
                "Total Invested": f"${pos2.total_invested:,.2f}",
                "Num Trades": len(pos2.trades)
            })
            return True
        else:
            log_error("Position data mismatch")
            return False

    except Exception as e:
        log_error(f"Persistence test failed: {e}")
        return False


def main():
    """Run all Phase 2 tests."""
    console.clear()
    print_header("POLYMARKET AGENT - PHASE 2 POSITION MANAGER TEST")
    console.print()

    tests = [
        ("Position Creation", test_position_creation),
        ("PnL Calculations", test_pnl_calculations),
        ("Hedging Simulation", test_hedging_simulation),
        ("Stop Loss Simulation", test_stop_loss_simulation),
        ("Position Persistence", test_persistence),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            console.print()
        except Exception as e:
            log_error(f"{test_name} test crashed: {e}")
            results.append((test_name, False))
            console.print()

    # Summary
    print_header("Test Summary")
    for test_name, result in results:
        status = "[green]✓ PASS[/green]" if result else "[red]✗ FAIL[/red]"
        console.print(f"{status} - {test_name}")

    all_passed = all(result for _, result in results)

    console.print()

    if all_passed:
        log_success("All Phase 2 tests passed!")
    else:
        log_error("Some tests failed")

    # Clean up test files
    for f in ["position_test.json", "position_stoploss_test.json", "position_persist_test.json"]:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    main()
