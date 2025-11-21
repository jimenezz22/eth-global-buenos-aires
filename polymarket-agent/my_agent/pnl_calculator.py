"""PnL calculation utilities and helpers."""

from typing import Dict, Tuple


def calculate_hedge_shares(
    yes_shares: float,
    sell_percentage: float,
    yes_sell_price: float,
    no_buy_price: float
) -> Tuple[float, float, float]:
    """
    Calculate how many YES shares to sell and NO shares to buy for hedging.

    Args:
        yes_shares: Current YES shares held
        sell_percentage: Percentage of YES to sell (0.0-1.0)
        yes_sell_price: Price to sell YES at
        no_buy_price: Price to buy NO at

    Returns:
        Tuple of (yes_to_sell, no_to_buy, usdc_proceeds)
    """
    # Shares to sell
    yes_to_sell = yes_shares * sell_percentage

    # USDC proceeds from selling YES
    usdc_proceeds = yes_to_sell * yes_sell_price

    # NO shares we can buy with proceeds
    no_to_buy = usdc_proceeds / no_buy_price

    return (yes_to_sell, no_to_buy, usdc_proceeds)


def calculate_final_pnl_scenarios(
    yes_shares: float,
    no_shares: float,
    total_cost: float
) -> Dict[str, float]:
    """
    Calculate PnL for both outcome scenarios.

    Args:
        yes_shares: YES shares held
        no_shares: NO shares held
        total_cost: Total cost basis

    Returns:
        Dictionary with PnL for both outcomes
    """
    # If YES wins: YES pays $1, NO pays $0
    pnl_if_yes_wins = (yes_shares * 1.0) - total_cost

    # If NO wins: NO pays $1, YES pays $0
    pnl_if_no_wins = (no_shares * 1.0) - total_cost

    # Guaranteed minimum (worst case)
    guaranteed_min = min(pnl_if_yes_wins, pnl_if_no_wins)

    # Best case
    best_case = max(pnl_if_yes_wins, pnl_if_no_wins)

    return {
        "pnl_if_yes_wins": pnl_if_yes_wins,
        "pnl_if_no_wins": pnl_if_no_wins,
        "guaranteed_min": guaranteed_min,
        "best_case": best_case,
        "is_hedged": yes_shares > 0 and no_shares > 0,
        "is_profitable": guaranteed_min > 0
    }


def calculate_breakeven_prices(
    yes_shares: float,
    no_shares: float,
    avg_cost_yes: float,
    avg_cost_no: float
) -> Dict[str, float]:
    """
    Calculate breakeven prices for current position.

    Args:
        yes_shares: YES shares held
        no_shares: NO shares held
        avg_cost_yes: Average cost per YES share
        avg_cost_no: Average cost per NO share

    Returns:
        Dictionary with breakeven metrics
    """
    total_cost = (yes_shares * avg_cost_yes) + (no_shares * avg_cost_no)

    # Breakeven if we only sell YES
    breakeven_yes = total_cost / yes_shares if yes_shares > 0 else 0

    # Breakeven if we only sell NO
    breakeven_no = total_cost / no_shares if no_shares > 0 else 0

    return {
        "breakeven_yes_price": breakeven_yes,
        "breakeven_no_price": breakeven_no,
        "total_cost": total_cost
    }


def calculate_roi(
    current_value: float,
    total_invested: float,
    total_withdrawn: float = 0.0
) -> Dict[str, float]:
    """
    Calculate return on investment metrics.

    Args:
        current_value: Current portfolio value
        total_invested: Total USDC invested
        total_withdrawn: Total USDC withdrawn

    Returns:
        ROI metrics
    """
    net_pnl = (current_value + total_withdrawn) - total_invested
    roi_pct = (net_pnl / total_invested * 100) if total_invested > 0 else 0

    return {
        "net_pnl": net_pnl,
        "roi_percent": roi_pct,
        "total_return": current_value + total_withdrawn,
        "profit_factor": (current_value + total_withdrawn) / total_invested if total_invested > 0 else 0
    }


def calculate_optimal_hedge_ratio(
    yes_price: float,
    no_price: float,
    target_profit_lock: float = 1.0
) -> float:
    """
    Calculate optimal percentage of YES to sell for hedging.

    Args:
        yes_price: Current YES price
        no_price: Current NO price
        target_profit_lock: Desired profit lock multiplier (1.0 = full hedge)

    Returns:
        Optimal sell percentage (0.0-1.0)
    """
    # For binary markets where YES + NO ≈ 1.0
    # To fully hedge: sell enough YES to buy equal NO shares
    # This ensures profit regardless of outcome

    # If selling X% of YES at price P_yes
    # Buy shares = (X * P_yes) / P_no
    # For perfect hedge: want resulting YES shares ≈ NO shares

    # Simplified: sell 100% for maximum hedge efficiency
    # (can be tuned based on risk tolerance)

    return 1.0 * target_profit_lock


def calculate_slippage_impact(
    shares: float,
    expected_price: float,
    actual_price: float
) -> Dict[str, float]:
    """
    Calculate slippage impact on trade.

    Args:
        shares: Number of shares traded
        expected_price: Expected price
        actual_price: Actual executed price

    Returns:
        Slippage metrics
    """
    expected_value = shares * expected_price
    actual_value = shares * actual_price

    slippage_usd = actual_value - expected_value
    slippage_pct = (slippage_usd / expected_value * 100) if expected_value > 0 else 0

    return {
        "expected_value": expected_value,
        "actual_value": actual_value,
        "slippage_usd": slippage_usd,
        "slippage_percent": slippage_pct
    }


def format_pnl(pnl: float, include_sign: bool = True) -> str:
    """
    Format PnL for display.

    Args:
        pnl: PnL amount
        include_sign: Include + for positive values

    Returns:
        Formatted string
    """
    sign = "+" if pnl > 0 and include_sign else ""
    return f"{sign}${pnl:,.2f}"


def format_roi(roi_pct: float, include_sign: bool = True) -> str:
    """
    Format ROI percentage for display.

    Args:
        roi_pct: ROI percentage
        include_sign: Include + for positive values

    Returns:
        Formatted string
    """
    sign = "+" if roi_pct > 0 and include_sign else ""
    return f"{sign}{roi_pct:.2f}%"
