"""Logging utilities using Rich library."""

from datetime import datetime
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from my_agent.utils.constants import (
    DEFAULT_STOP_LOSS_PROBABILITY,
    DEFAULT_TAKE_PROFIT_PROBABILITY,
    TIMESTAMP_FORMAT_SHORT,
    DisplayColor,
    DisplayIcon,
)

# Global console instance
console = Console()


# ============================================================================
# BASIC LOGGING FUNCTIONS
# ============================================================================


def log_info(message: str) -> None:
    """
    Log informational message.

    Args:
        message: The message to log
    """
    console.print(f"[{DisplayColor.INFO}]{DisplayIcon.INFO}[/{DisplayColor.INFO}] {message}")


def log_success(message: str) -> None:
    """
    Log success message.

    Args:
        message: The message to log
    """
    console.print(f"[{DisplayColor.SUCCESS}]{DisplayIcon.SUCCESS}[/{DisplayColor.SUCCESS}] {message}")


def log_warning(message: str) -> None:
    """
    Log warning message.

    Args:
        message: The message to log
    """
    console.print(f"[{DisplayColor.WARNING}]{DisplayIcon.WARNING}[/{DisplayColor.WARNING}] {message}")


def log_error(message: str) -> None:
    """
    Log error message.

    Args:
        message: The message to log
    """
    console.print(f"[{DisplayColor.ERROR}]{DisplayIcon.ERROR}[/{DisplayColor.ERROR}] {message}")


def log_trade(action: str, details: str) -> None:
    """
    Log trade action with timestamp.

    Args:
        action: The trade action (e.g., "BUY", "SELL")
        details: Additional trade details
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT_SHORT)
    console.print(
        f"[{DisplayColor.HIGHLIGHT}][{timestamp}][/{DisplayColor.HIGHLIGHT}] "
        f"[bold]{action}[/bold]: {details}"
    )


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================


def print_header(title: str) -> None:
    """
    Print a formatted header panel.

    Args:
        title: The header title text
    """
    console.print(Panel.fit(f"[bold {DisplayColor.HIGHLIGHT}]{title}[/bold {DisplayColor.HIGHLIGHT}]"))


def print_status_table(data: Dict[str, str]) -> None:
    """
    Print a status table with key-value pairs.

    Args:
        data: Dictionary of key-value pairs to display
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style=DisplayColor.HIGHLIGHT, no_wrap=True)
    table.add_column(style="white")

    for key, value in data.items():
        table.add_row(f"{key}:", str(value))

    console.print(table)


def print_market_data(timestamp: str, yes_price: float, volume: Optional[float] = None) -> None:
    """
    Print formatted market data with color-coded probability.

    Args:
        timestamp: The timestamp string
        yes_price: YES price (probability)
        volume: Optional trading volume
    """
    probability_pct = yes_price * 100
    price_color = _get_price_color(yes_price)

    parts = [
        f"[{DisplayColor.DIM}]{timestamp}[/{DisplayColor.DIM}]",
        f"YES: [bold {price_color}]{yes_price:.4f}[/bold {price_color}] ({probability_pct:.2f}%)"
    ]

    if volume is not None:
        parts.append(f"Volume: [{DisplayColor.HIGHLIGHT}]${volume:,.0f}[/{DisplayColor.HIGHLIGHT}]")

    console.print(" | ".join(parts))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_price_color(price: float) -> str:
    """
    Determine color for price display based on thresholds.

    Args:
        price: The price/probability value

    Returns:
        Color name for Rich console
    """
    if price >= DEFAULT_TAKE_PROFIT_PROBABILITY:
        return DisplayColor.PRICE_HIGH

    if price <= DEFAULT_STOP_LOSS_PROBABILITY:
        return DisplayColor.PRICE_LOW

    return DisplayColor.PRICE_MEDIUM
