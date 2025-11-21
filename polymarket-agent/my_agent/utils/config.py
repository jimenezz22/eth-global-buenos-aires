"""Configuration management for the Polymarket Agent."""

import os
from typing import ClassVar, List, Tuple

from dotenv import load_dotenv

from my_agent.utils.constants import (
    DEFAULT_ENTRY_PROBABILITY,
    DEFAULT_HEDGE_SELL_PERCENT,
    DEFAULT_MAX_SLIPPAGE_PERCENT,
    DEFAULT_MIN_LIQUIDITY_USD,
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_POLYGON_RPC_URL,
    DEFAULT_STOP_LOSS_PROBABILITY,
    DEFAULT_TAKE_PROFIT_PROBABILITY,
    POLYGON_MAINNET_CHAIN_ID,
    USDC_ADDRESS_POLYGON,
)

# Load environment variables once at module import
load_dotenv()


class Config:
    """
    Application configuration loaded from environment variables.

    This class follows the Single Responsibility Principle by only
    handling configuration loading and validation. Display logic
    has been extracted to ConfigDisplay class.
    """

    # Core credentials
    PRIVATE_KEY: ClassVar[str] = (
        os.getenv("PRIVATE_KEY")
        or os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")
    )

    POLYGON_RPC_URL: ClassVar[str] = os.getenv(
        "POLYGON_RPC_URL",
        DEFAULT_POLYGON_RPC_URL
    )

    CHAIN_ID: ClassVar[int] = int(
        os.getenv("CHAIN_ID", str(POLYGON_MAINNET_CHAIN_ID))
    )

    # API keys
    OPENAI_API_KEY: ClassVar[str] = os.getenv("OPENAI_API_KEY", "")

    # Market configuration
    MARKET_CONDITION_ID: ClassVar[str] = os.getenv("MARKET_CONDITION_ID", "")
    MARKET_QUESTION: ClassVar[str] = os.getenv(
        "MARKET_QUESTION",
        "Buffalo Bills to win Super Bowl 2026"
    )

    # Strategy parameters
    ENTRY_PROBABILITY: ClassVar[float] = float(
        os.getenv("ENTRY_PROBABILITY", str(DEFAULT_ENTRY_PROBABILITY))
    )

    TAKE_PROFIT_PROBABILITY: ClassVar[float] = float(
        os.getenv("TAKE_PROFIT_PROBABILITY", str(DEFAULT_TAKE_PROFIT_PROBABILITY))
    )

    STOP_LOSS_PROBABILITY: ClassVar[float] = float(
        os.getenv("STOP_LOSS_PROBABILITY", str(DEFAULT_STOP_LOSS_PROBABILITY))
    )

    HEDGE_SELL_PERCENT: ClassVar[float] = float(
        os.getenv("HEDGE_SELL_PERCENT", str(DEFAULT_HEDGE_SELL_PERCENT))
    )

    POLL_INTERVAL_SECONDS: ClassVar[int] = int(
        os.getenv("POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL_SECONDS))
    )

    # Risk management
    MAX_SLIPPAGE_PERCENT: ClassVar[float] = float(
        os.getenv("MAX_SLIPPAGE_PERCENT", str(DEFAULT_MAX_SLIPPAGE_PERCENT))
    )

    MIN_LIQUIDITY_USD: ClassVar[float] = float(
        os.getenv("MIN_LIQUIDITY_USD", str(DEFAULT_MIN_LIQUIDITY_USD))
    )

    # Execution mode
    DEMO_MODE: ClassVar[bool] = (
        os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    )

    # Contract addresses
    USDC_ADDRESS: ClassVar[str] = USDC_ADDRESS_POLYGON

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present and properly formatted.

        Returns:
            bool: True if validation passes

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check required fields
        missing_fields = cls._check_required_fields()
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}"
            )

        # Normalize private key format
        cls._normalize_private_key()

        # Validate thresholds
        cls._validate_thresholds()

        return True

    @classmethod
    def _check_required_fields(cls) -> List[str]:
        """Check for missing required configuration fields."""
        required_fields: List[Tuple[str, str]] = [
            ("PRIVATE_KEY", cls.PRIVATE_KEY),
            ("POLYGON_RPC_URL", cls.POLYGON_RPC_URL),
        ]

        return [name for name, value in required_fields if not value]

    @classmethod
    def _normalize_private_key(cls) -> None:
        """Ensure private key has 0x prefix."""
        if cls.PRIVATE_KEY and not cls.PRIVATE_KEY.startswith("0x"):
            cls.PRIVATE_KEY = f"0x{cls.PRIVATE_KEY}"

    @classmethod
    def _validate_thresholds(cls) -> None:
        """Validate probability thresholds are in correct ranges."""
        if not (0 < cls.STOP_LOSS_PROBABILITY < cls.TAKE_PROFIT_PROBABILITY < 1):
            raise ValueError(
                f"Invalid thresholds: STOP_LOSS ({cls.STOP_LOSS_PROBABILITY}) "
                f"< TAKE_PROFIT ({cls.TAKE_PROFIT_PROBABILITY}) required"
            )

        if not (0 < cls.HEDGE_SELL_PERCENT <= 1):
            raise ValueError(
                f"Invalid HEDGE_SELL_PERCENT: {cls.HEDGE_SELL_PERCENT} "
                "(must be between 0 and 1)"
            )


class ConfigDisplay:
    """
    Handles configuration display logic (separated from Config for SRP).
    """

    @staticmethod
    def format_private_key(private_key: str, prefix_len: int = 6, suffix_len: int = 4) -> str:
        """
        Format private key for safe display.

        Args:
            private_key: The private key to format
            prefix_len: Number of characters to show at start
            suffix_len: Number of characters to show at end

        Returns:
            Masked private key string
        """
        if not private_key:
            return "NOT SET"

        return f"{private_key[:prefix_len]}...{private_key[-suffix_len:]}"

    @staticmethod
    def format_condition_id(condition_id: str, prefix_len: int = 10, suffix_len: int = 6) -> str:
        """
        Format condition ID for display.

        Args:
            condition_id: The condition ID to format
            prefix_len: Number of characters to show at start
            suffix_len: Number of characters to show at end

        Returns:
            Formatted condition ID string
        """
        if not condition_id:
            return "NOT SET"

        return f"{condition_id[:prefix_len]}...{condition_id[-suffix_len:]}"

    @staticmethod
    def get_network_name(chain_id: int) -> str:
        """Get human-readable network name from chain ID."""
        return "Polygon Mainnet" if chain_id == POLYGON_MAINNET_CHAIN_ID else "Polygon Amoy Testnet"

    @classmethod
    def display(cls, config: Config) -> str:
        """
        Display configuration with sensitive data masked.

        Args:
            config: Config instance to display

        Returns:
            Formatted configuration string
        """
        pk_preview = cls.format_private_key(config.PRIVATE_KEY)
        condition_preview = cls.format_condition_id(config.MARKET_CONDITION_ID)
        network_name = cls.get_network_name(config.CHAIN_ID)
        rpc_preview = f"{config.POLYGON_RPC_URL[:50]}..." if len(config.POLYGON_RPC_URL) > 50 else config.POLYGON_RPC_URL
        execution_mode = "ENABLED (No real trades)" if config.DEMO_MODE else "DISABLED (Real trades!)"

        return f"""
╔══════════════════════════════════════════════════════════╗
║              POLYMARKET AGENT CONFIGURATION              ║
╚══════════════════════════════════════════════════════════╝

Network Configuration:
  • Chain: {network_name}
  • Chain ID: {config.CHAIN_ID}
  • RPC: {rpc_preview}
  • Private Key: {pk_preview}

Market Configuration:
  • Condition ID: {condition_preview}

Strategy Parameters:
  • Entry Probability: {config.ENTRY_PROBABILITY * 100:.1f}%
  • Take Profit: {config.TAKE_PROFIT_PROBABILITY * 100:.1f}%
  • Stop Loss: {config.STOP_LOSS_PROBABILITY * 100:.1f}%
  • Hedge Sell %: {config.HEDGE_SELL_PERCENT * 100:.0f}%
  • Poll Interval: {config.POLL_INTERVAL_SECONDS}s

Risk Management:
  • Max Slippage: {config.MAX_SLIPPAGE_PERCENT}%
  • Min Liquidity: ${config.MIN_LIQUIDITY_USD:,.0f}

Execution Mode:
  • Demo Mode: {execution_mode}
"""


# Singleton instance
config = Config()
