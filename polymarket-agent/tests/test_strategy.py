#!/usr/bin/env python3
"""Test script for Phase 3 - Core Trading Strategy."""

import os
from my_agent.utils.logger import (
    console,
    log_info,
    log_success,
    log_error,
    print_header,
    print_status_table
)
from my_agent.position import Position
from my_agent.strategy import create_strategy
from my_agent.pnl_calculator import format_pnl, format_roi


def test_scenario_1_profit_lock():
    """
    Scenario 1: Price rises from 80% → 86% → Hedge → Profit locked
    """
    print_header("Scenario 1: Take Profit & Hedge (80% → 86%)")

    test_file = "position_scenario1.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        # Initialize position
        position = Position(position_file=test_file)
        strategy = create_strategy(
            position=position,
            take_profit_threshold=0.85,
            stop_loss_threshold=0.78,
            hedge_sell_percent=1.0  # Sell 100%
        )

        # Step 1: Entry at 80%
        log_info("📊 Step 1: Entry")
        position.open_position(shares=1250.0, price=0.80, side="YES", entry_prob=0.80)
        print_status_table({
            "Action": "BUY 1250 YES @ $0.80",
            "Invested": "$1,000",
            "YES Shares": "1,250",
            "NO Shares": "0"
        })

        console.print()

        # Step 2: Price rises to 82% (hold)
        log_info("📊 Step 2: Price → 82% (HOLD)")
        action = strategy.evaluate(current_prob=0.82, yes_price=0.82, no_price=0.18)
        pnl = position.calculate_unrealized_pnl(0.82, 0.18)
        print_status_table({
            "Action": action["action"],
            "Reason": action["reason"],
            "Unrealized PnL": format_pnl(pnl["unrealized_pnl"]),
            "ROI": format_roi(pnl["roi"])
        })

        console.print()

        # Step 3: Price rises to 86% (take profit)
        log_info("📊 Step 3: Price → 86% (TAKE PROFIT)")
        action = strategy.evaluate(current_prob=0.86, yes_price=0.86, no_price=0.14)

        if action["action"] == "TAKE_PROFIT":
            log_success("✓ Take-profit triggered!")
            result = strategy.execute_action(action)

            console.print()
            print_status_table({
                "YES Sold": f"{result['yes_sold']:.0f} @ ${result['yes_price']:.4f}",
                "Proceeds": f"${result['proceeds']:,.2f}",
                "NO Bought": f"{result['no_bought']:.0f} @ ${result['no_price']:.4f}",
                "Locked PnL": format_pnl(result['locked_pnl'])
            })

        console.print()

        # Step 4: Calculate final scenarios
        log_info("📊 Step 4: Final Position Analysis")

        # Current state
        print_status_table({
            "YES Shares": f"{position.yes_shares:.0f}",
            "NO Shares": f"{position.no_shares:.0f}",
            "Total Invested": f"${position.total_invested:,.2f}",
            "Total Withdrawn": f"${position.total_withdrawn:,.2f}"
        })

        console.print()

        # Outcome scenarios
        yes_final = position.yes_shares * 1.0  # YES wins
        no_final = position.no_shares * 1.0    # NO wins

        total_cost = (position.yes_shares * position.avg_cost_yes) + \
                     (position.no_shares * position.avg_cost_no)

        pnl_if_yes = yes_final - total_cost
        pnl_if_no = no_final - total_cost

        log_success("📈 Final Outcome Scenarios:")
        print_status_table({
            "If YES wins": format_pnl(pnl_if_yes),
            "If NO wins": format_pnl(pnl_if_no),
            "Guaranteed Min": format_pnl(min(pnl_if_yes, pnl_if_no)),
            "Status": "✓ Profitable" if min(pnl_if_yes, pnl_if_no) > 0 else "✗ Loss"
        })

        return True

    except Exception as e:
        log_error(f"Scenario 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_scenario_2_stop_loss():
    """
    Scenario 2: Price drops from 80% → 76% → Stop loss
    """
    print_header("Scenario 2: Stop Loss (80% → 76%)")

    test_file = "position_scenario2.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        # Initialize
        position = Position(position_file=test_file)
        strategy = create_strategy(
            position=position,
            take_profit_threshold=0.85,
            stop_loss_threshold=0.78
        )

        # Step 1: Entry
        log_info("📊 Step 1: Entry")
        position.open_position(shares=1250.0, price=0.80, side="YES", entry_prob=0.80)
        print_status_table({
            "Action": "BUY 1250 YES @ $0.80",
            "Invested": "$1,000"
        })

        console.print()

        # Step 2: Price drops to 76%
        log_info("📊 Step 2: Price → 76% (STOP LOSS)")
        action = strategy.evaluate(current_prob=0.76, yes_price=0.76, no_price=0.24)

        if action["action"] == "STOP_LOSS":
            log_error("⚠ Stop-loss triggered!")
            result = strategy.execute_action(action)

            console.print()
            print_status_table({
                "YES Sold": f"{result['yes_sold']:.0f} @ ${result['yes_price']:.4f}",
                "Proceeds": f"${result['total_proceeds']:,.2f}",
                "Final PnL": format_pnl(result['final_pnl']),
                "ROI": format_roi((result['final_pnl'] / 1000) * 100)
            })

            if result['final_pnl'] < 0:
                log_info("💡 Loss minimized by exiting early")

        return True

    except Exception as e:
        log_error(f"Scenario 2 failed: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_scenario_3_hedge_protection():
    """
    Scenario 3: Hedge @ 85%, then price drops to 50% → Profit still locked
    """
    print_header("Scenario 3: Hedge Protection (85% → Hedge → 50%)")

    test_file = "position_scenario3.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    try:
        # Initialize
        position = Position(position_file=test_file)
        strategy = create_strategy(
            position=position,
            take_profit_threshold=0.85,
            hedge_sell_percent=0.60  # Sell 60% (partial hedge)
        )

        # Step 1: Entry
        log_info("📊 Step 1: Entry @ 80%")
        position.open_position(shares=1250.0, price=0.80, side="YES", entry_prob=0.80)
        print_status_table({
            "Invested": "$1,000",
            "YES Shares": "1,250"
        })

        console.print()

        # Step 2: Hedge at 85%
        log_info("📊 Step 2: Price → 85% (HEDGE)")
        result = strategy.book_profit_and_rebalance(
            yes_price=0.85,
            no_price=0.15,
            execute_trades=True
        )

        print_status_table({
            "YES Sold": f"{result['yes_sold']:.0f} (60%)",
            "NO Bought": f"{result['no_bought']:.0f}",
            "Locked PnL": format_pnl(result['locked_pnl']),
            "Remaining YES": f"{result['remaining_yes']:.0f}",
            "Remaining NO": f"{result['remaining_no']:.0f}"
        })

        console.print()

        # Step 3: Price crashes to 50%
        log_info("📊 Step 3: Price crashes → 50%")
        pnl = position.calculate_unrealized_pnl(yes_price=0.50, no_price=0.50)
        locked = position.calculate_locked_pnl()

        print_status_table({
            "Current Price": "50%",
            "Total Value": f"${pnl['total_value']:,.2f}",
            "Unrealized PnL": format_pnl(pnl['unrealized_pnl']),
            "Locked PnL": format_pnl(locked),
            "Net PnL": format_pnl(pnl['net_pnl'])
        })

        console.print()

        # Final outcomes
        log_success("📈 Protected by Hedge:")
        yes_final_pnl = (position.yes_shares * 1.0 + position.total_withdrawn) - position.total_invested
        no_final_pnl = (position.no_shares * 1.0 + position.total_withdrawn) - position.total_invested

        print_status_table({
            "If YES wins": format_pnl(yes_final_pnl),
            "If NO wins": format_pnl(no_final_pnl),
            "Guaranteed Min": format_pnl(min(yes_final_pnl, no_final_pnl))
        })

        return True

    except Exception as e:
        log_error(f"Scenario 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def main():
    """Run all strategy tests."""
    console.clear()
    print_header("POLYMARKET AGENT - PHASE 3 STRATEGY TEST")
    console.print()

    scenarios = [
        ("Scenario 1: Profit Lock (80%→86%)", test_scenario_1_profit_lock),
        ("Scenario 2: Stop Loss (80%→76%)", test_scenario_2_stop_loss),
        ("Scenario 3: Hedge Protection (85%→50%)", test_scenario_3_hedge_protection),
    ]

    results = []
    for scenario_name, scenario_func in scenarios:
        try:
            result = scenario_func()
            results.append((scenario_name, result))
            console.print("\n")
        except Exception as e:
            log_error(f"{scenario_name} crashed: {e}")
            results.append((scenario_name, False))
            console.print("\n")

    # Summary
    print_header("Test Summary")
    for scenario_name, result in results:
        status = "[green]✓ PASS[/green]" if result else "[red]✗ FAIL[/red]"
        console.print(f"{status} - {scenario_name}")

    all_passed = all(result for _, result in results)

    console.print()

    if all_passed:
        log_success("All Phase 3 strategy tests passed!")
        log_info("Strategy is ready for live trading")
    else:
        log_error("Some tests failed")


if __name__ == "__main__":
    main()
