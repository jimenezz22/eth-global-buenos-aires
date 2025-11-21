"""Application-wide constants to avoid magic numbers and strings."""

from enum import Enum
from typing import Final


# ============================================================================
# THRESHOLD CONSTANTS
# ============================================================================

# Default probability thresholds (can be overridden by config)
DEFAULT_ENTRY_PROBABILITY: Final[float] = 0.80
DEFAULT_TAKE_PROFIT_PROBABILITY: Final[float] = 0.85
DEFAULT_STOP_LOSS_PROBABILITY: Final[float] = 0.78
DEFAULT_HEDGE_SELL_PERCENT: Final[float] = 1.0

# Risk management thresholds
DEFAULT_MAX_SLIPPAGE_PERCENT: Final[float] = 2.0
DEFAULT_MIN_LIQUIDITY_USD: Final[float] = 5000.0

# Polling configuration
DEFAULT_POLL_INTERVAL_SECONDS: Final[int] = 20
MAX_POLL_INTERVAL_SECONDS: Final[int] = 300  # 5 minutes

# Retry configuration
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_INITIAL_DELAY_SECONDS: Final[float] = 1.0
DEFAULT_BACKOFF_FACTOR: Final[float] = 2.0


# ============================================================================
# MARKET DATA VALIDATION
# ============================================================================

# Binary market prices should sum to approximately 1.0
MIN_PRICE_SUM: Final[float] = 0.95
MAX_PRICE_SUM: Final[float] = 1.05

# Price bounds
MIN_PRICE: Final[float] = 0.0
MAX_PRICE: Final[float] = 1.0


# ============================================================================
# BLOCKCHAIN CONSTANTS
# ============================================================================

# Polygon network
POLYGON_MAINNET_CHAIN_ID: Final[int] = 137
POLYGON_AMOY_TESTNET_CHAIN_ID: Final[int] = 80002

# USDC contract address (Polygon Mainnet)
USDC_ADDRESS_POLYGON: Final[str] = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Default RPC URL
DEFAULT_POLYGON_RPC_URL: Final[str] = "https://polygon-mainnet.g.alchemy.com/v2/demo"


# ============================================================================
# DISPLAY CONSTANTS
# ============================================================================

class DisplayColor(str, Enum):
    """Color codes for Rich console output."""

    INFO = "blue"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    HIGHLIGHT = "cyan"
    DIM = "dim"

    # Price-based colors
    PRICE_HIGH = "green"    # Above take-profit threshold
    PRICE_MEDIUM = "yellow" # Between thresholds
    PRICE_LOW = "red"       # Below stop-loss threshold


class DisplayIcon(str, Enum):
    """Unicode icons for console output."""

    INFO = "ℹ"
    SUCCESS = "✓"
    WARNING = "⚠"
    ERROR = "✗"
    TRADE = "💰"
    CHART = "📊"
    POSITION = "💼"
    TARGET = "🎯"
    ROBOT = "🤖"
    LOCK = "🔒"
    FIRE = "🔥"
    MEMO = "📝"


# ============================================================================
# ACTION TYPES
# ============================================================================

class ActionType(str, Enum):
    """Strategy action types."""

    WAIT = "WAIT"
    HOLD = "HOLD"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    HEDGE = "HEDGE"


class TradeType(str, Enum):
    """Trade execution types."""

    BUY = "BUY"
    SELL = "SELL"


class PositionSide(str, Enum):
    """Position side (YES or NO)."""

    YES = "YES"
    NO = "NO"


# ============================================================================
# FORMATTING CONSTANTS
# ============================================================================

# Private key display format
PRIVATE_KEY_PREFIX_LENGTH: Final[int] = 6
PRIVATE_KEY_SUFFIX_LENGTH: Final[int] = 4

# Condition ID display format
CONDITION_ID_PREFIX_LENGTH: Final[int] = 10
CONDITION_ID_SUFFIX_LENGTH: Final[int] = 6

# Timestamp formats
TIMESTAMP_FORMAT_DISPLAY: Final[str] = "%Y-%m-%d %H:%M:%S UTC"
TIMESTAMP_FORMAT_SHORT: Final[str] = "%H:%M:%S"

# Number formatting
PERCENTAGE_DECIMAL_PLACES: Final[int] = 2
CURRENCY_DECIMAL_PLACES: Final[int] = 2
PRICE_DECIMAL_PLACES: Final[int] = 4


# ============================================================================
# FILE PATHS
# ============================================================================

DEFAULT_POSITION_FILE: Final[str] = "position.json"
ENV_FILE_NAME: Final[str] = ".env"


# ============================================================================
# AI ADVISOR CONSTANTS
# ============================================================================

class AIProvider(str, Enum):
    """Supported AI providers."""

    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"


# Default models for each provider
DEFAULT_GEMINI_MODEL: Final[str] = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL: Final[str] = "gpt-3.5-turbo"
DEFAULT_CLAUDE_MODEL: Final[str] = "claude-3-haiku-20240307"

# AI confidence thresholds
MIN_AI_OVERRIDE_CONFIDENCE: Final[int] = 70
AI_TEMPERATURE: Final[float] = 0.3
