"""Helper utilities for the agent."""

import signal
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple, Type

from rich.table import Table

from my_agent.utils.constants import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_INITIAL_DELAY_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_STOP_LOSS_PROBABILITY,
    DEFAULT_TAKE_PROFIT_PROBABILITY,
    DisplayColor,
    MAX_PRICE,
    MAX_PRICE_SUM,
    MIN_PRICE,
    MIN_PRICE_SUM,
    TIMESTAMP_FORMAT_DISPLAY,
)
from my_agent.utils.logger import console


# ============================================================================
# SIGNAL HANDLING
# ============================================================================


class GracefulKiller:
    """
    Handle graceful shutdown on SIGINT/SIGTERM signals.

    This allows the agent to clean up resources and save state
    before exiting when Ctrl+C is pressed or SIGTERM is received.
    """

    def __init__(self) -> None:
        """Initialize signal handlers."""
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args: Any) -> None:
        """
        Set kill flag when signal is received.

        Args:
            *args: Signal handler arguments (unused)
        """
        self.kill_now = True


# ============================================================================
# RETRY LOGIC
# ============================================================================


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY_SECONDS,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry (must take no arguments)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries are exhausted
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                # Last attempt failed, re-raise the exception
                raise e

            # Wait before retrying
            time.sleep(delay)
            delay *= backoff_factor

    # This should never be reached due to the raise above
    return None


# ============================================================================
# FORMATTING UTILITIES
# ============================================================================


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format timestamp for display.

    Args:
        dt: Datetime object (default: current UTC time)

    Returns:
        Formatted timestamp string (e.g., "2025-01-15 14:30:00 UTC")
    """
    if dt is None:
        dt = datetime.utcnow()

    return dt.strftime(TIMESTAMP_FORMAT_DISPLAY)


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 15m 30s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    duration_parts = []

    if hours > 0:
        duration_parts.append(f"{hours}h")
    if minutes > 0:
        duration_parts.append(f"{minutes}m")
    if secs > 0 or not duration_parts:
        duration_parts.append(f"{secs}s")

    return " ".join(duration_parts)


# ============================================================================
# TABLE CREATION
# ============================================================================


def create_status_table(data: Dict[str, str], title: str = "Status") -> Table:
    """
    Create a Rich table for status display.

    Args:
        data: Dictionary of key-value pairs
        title: Table title

    Returns:
        Rich Table object ready to be printed
    """
    table = Table(title=title, show_header=True, header_style=f"bold {DisplayColor.HIGHLIGHT}")
    table.add_column("Metric", style=DisplayColor.HIGHLIGHT, no_wrap=True)
    table.add_column("Value", style="white")

    for key, value in data.items():
        table.add_row(key, str(value))

    return table


# ============================================================================
# AGENT STATUS DISPLAY
# ============================================================================


def print_agent_status(
    current_prob: float,
    yes_price: float,
    no_price: float,
    position_summary: Dict[str, Any],
    action: Dict[str, Any]
) -> None:
    """
    Print comprehensive agent status including market data, position, and action.

    Args:
        current_prob: Current YES probability
        yes_price: Current YES price
        no_price: Current NO price
        position_summary: Position summary dictionary
        action: Recommended action dictionary
    """
    _print_market_data_section(current_prob, yes_price, no_price)
    _print_position_section(position_summary)
    _print_action_section(action)


def _print_market_data_section(current_prob: float, yes_price: float, no_price: float) -> None:
    """Print market data table."""
    market_table = Table(title=f"📊 Market Data", show_header=False, box=None)
    market_table.add_column(style=DisplayColor.HIGHLIGHT)
    market_table.add_column(style="white")

    prob_color = _get_probability_color(current_prob)

    market_table.add_row("Current Probability", f"[{prob_color}]{current_prob * 100:.2f}%[/{prob_color}]")
    market_table.add_row("YES Price", f"${yes_price:.4f}")
    market_table.add_row("NO Price", f"${no_price:.4f}")

    console.print(market_table)
    console.print()


def _print_position_section(position_summary: Dict[str, Any]) -> None:
    """Print position summary table if position exists."""
    if position_summary["yes_shares"] <= 0 and position_summary["no_shares"] <= 0:
        return

    position_table = Table(title="💼 Position", show_header=False, box=None)
    position_table.add_column(style=DisplayColor.HIGHLIGHT)
    position_table.add_column(style="white")

    position_table.add_row("YES Shares", f"{position_summary['yes_shares']:.0f}")
    position_table.add_row("NO Shares", f"{position_summary['no_shares']:.0f}")
    position_table.add_row("Total Invested", f"${position_summary['total_invested']:,.2f}")
    position_table.add_row("Total Withdrawn", f"${position_summary['total_withdrawn']:,.2f}")

    pnl_color = DisplayColor.SUCCESS if position_summary['net_pnl'] >= 0 else DisplayColor.ERROR
    position_table.add_row(
        "Net PnL",
        f"[{pnl_color}]${position_summary['net_pnl']:,.2f} ({position_summary['roi']:.2f}%)[/{pnl_color}]"
    )

    if position_summary.get('locked_pnl', 0) > 0:
        position_table.add_row(
            "Locked PnL",
            f"[{DisplayColor.SUCCESS}]${position_summary['locked_pnl']:,.2f}[/{DisplayColor.SUCCESS}]"
        )

    console.print(position_table)
    console.print()


def _print_action_section(action: Dict[str, Any]) -> None:
    """Print recommended action table."""
    action_table = Table(title="🎯 Recommended Action", show_header=False, box=None)
    action_table.add_column(style=DisplayColor.HIGHLIGHT)
    action_table.add_column(style="white")

    action_type = action["action"]
    action_color = _get_action_color(action_type)

    action_table.add_row("Action", f"[{action_color}]{action_type}[/{action_color}]")
    action_table.add_row("Reason", action["reason"])

    console.print(action_table)


def _get_probability_color(probability: float) -> str:
    """
    Get color for probability display based on thresholds.

    Args:
        probability: The probability value

    Returns:
        Color string for Rich console
    """
    if probability >= DEFAULT_TAKE_PROFIT_PROBABILITY:
        return DisplayColor.PRICE_HIGH

    if probability <= DEFAULT_STOP_LOSS_PROBABILITY:
        return DisplayColor.PRICE_LOW

    return DisplayColor.PRICE_MEDIUM


def _get_action_color(action_type: str) -> str:
    """
    Get color for action display.

    Args:
        action_type: The action type (WAIT, HOLD, TAKE_PROFIT, STOP_LOSS)

    Returns:
        Color string for Rich console
    """
    action_colors = {
        "TAKE_PROFIT": DisplayColor.SUCCESS,
        "STOP_LOSS": DisplayColor.ERROR,
        "HOLD": DisplayColor.WARNING,
        "WAIT": DisplayColor.WARNING,
    }

    return action_colors.get(action_type, DisplayColor.INFO)


# ============================================================================
# TIME CALCULATIONS
# ============================================================================


def calculate_sleep_until_next_poll(
    poll_interval: int,
    last_poll_time: float
) -> float:
    """
    Calculate seconds to sleep until next poll interval.

    Args:
        poll_interval: Desired poll interval in seconds
        last_poll_time: Timestamp of last poll (from time.time())

    Returns:
        Seconds to sleep (minimum 0)
    """
    elapsed = time.time() - last_poll_time
    sleep_time = max(0, poll_interval - elapsed)
    return sleep_time


# ============================================================================
# VALIDATION
# ============================================================================


def validate_market_data(yes_price: float, no_price: float) -> bool:
    """
    Validate that market data is within reasonable bounds.

    Args:
        yes_price: YES token price
        no_price: NO token price

    Returns:
        True if valid, False otherwise
    """
    # Prices must be between 0 and 1
    if not (MIN_PRICE <= yes_price <= MAX_PRICE and MIN_PRICE <= no_price <= MAX_PRICE):
        return False

    # For binary markets, YES + NO should be approximately 1.0
    total = yes_price + no_price
    if not (MIN_PRICE_SUM <= total <= MAX_PRICE_SUM):
        return False

    return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default on division by zero.

    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero

    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default

    return numerator / denominator
