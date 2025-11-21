"""
Polymarket AI Hedge Agent - Custom Hedging Strategy

This module extends the Polymarket Agents framework with intelligent hedging logic.
"""

from my_agent.strategy import TradingStrategy, create_strategy
from my_agent.position import Position, Trade, get_position
from my_agent.pnl_calculator import (
    calculate_hedge_shares,
    calculate_final_pnl_scenarios,
    calculate_breakeven_prices,
    calculate_roi,
    format_pnl,
    format_roi
)

__version__ = "1.0.0"

__all__ = [
    # Strategy
    "TradingStrategy",
    "create_strategy",

    # Position Management
    "Position",
    "Trade",
    "get_position",

    # PnL Calculations
    "calculate_hedge_shares",
    "calculate_final_pnl_scenarios",
    "calculate_breakeven_prices",
    "calculate_roi",
    "format_pnl",
    "format_roi",
]
