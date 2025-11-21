"""Position management and state persistence."""

import json
import os
from typing import Optional, Dict, List, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, asdict

from my_agent.utils.constants import PositionSide, TradeType

if TYPE_CHECKING:
    from agents.polymarket.polymarket import Polymarket


@dataclass
class Trade:
    """Represents a single trade."""
    timestamp: str
    side: str  # "YES" or "NO"
    shares: float
    price: float
    trade_type: str  # "BUY" or "SELL"
    usdc_amount: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Trade':
        """Create from dictionary."""
        return cls(**data)


class Position:
    """Manages trading position state and persistence."""

    def __init__(
        self,
        position_file: str = "position.json",
        polymarket_client: Optional["Polymarket"] = None,
        token_id: Optional[str] = None
    ):
        """
        Initialize position manager.

        Args:
            position_file: Path to position state file
            polymarket_client: Polymarket client for executing real trades
            token_id: Market token ID for trade execution
        """
        self.position_file = position_file
        self.polymarket_client = polymarket_client
        self.token_id = token_id

        # Position state
        self.yes_shares: float = 0.0
        self.no_shares: float = 0.0
        self.avg_cost_yes: float = 0.0
        self.avg_cost_no: float = 0.0
        self.entry_prob: float = 0.0
        self.entry_timestamp: Optional[str] = None
        self.total_invested: float = 0.0
        self.total_withdrawn: float = 0.0

        # Trade history
        self.trades: List[Trade] = []

        # Load existing position if file exists
        if os.path.exists(position_file):
            self.load()

    def open_position(
        self,
        shares: float,
        price: float,
        side: str = PositionSide.YES,
        entry_prob: Optional[float] = None,
        execute_trade: bool = False
    ):
        """
        Open initial position.

        Args:
            shares: Number of shares to buy
            price: Price per share
            side: Position side (PositionSide.YES or PositionSide.NO)
            entry_prob: Entry probability (optional)
            execute_trade: If True, execute real blockchain transaction
        """
        from my_agent.utils.logger import log_info, log_success, log_warning

        usdc_amount = shares * price

        # Execute real trade if enabled
        if execute_trade and self.polymarket_client and self.token_id:
            try:
                log_info(f"🔐 Executing REAL blockchain transaction...")
                log_info(f"   BUY {shares:.2f} {side} @ ${price:.4f} = ${usdc_amount:.2f} USDC")

                # Execute market buy order via Polymarket
                order_result = self.polymarket_client.execute_order(
                    price=price,
                    size=shares,
                    side=TradeType.BUY,
                    token_id=self.token_id
                )

                log_success(f"✅ Transaction successful! Order ID: {order_result}")

            except Exception as e:
                log_warning(f"❌ Blockchain transaction failed: {e}")
                raise
        else:
            log_info(f"📝 DEMO MODE: Simulating BUY {shares:.2f} {side} @ ${price:.4f}")

        self.total_invested += usdc_amount

        if side == PositionSide.YES:
            # Update average cost
            total_cost = (self.yes_shares * self.avg_cost_yes) + (shares * price)
            self.yes_shares += shares
            self.avg_cost_yes = total_cost / self.yes_shares if self.yes_shares > 0 else 0
        else:  # NO
            total_cost = (self.no_shares * self.avg_cost_no) + (shares * price)
            self.no_shares += shares
            self.avg_cost_no = total_cost / self.no_shares if self.no_shares > 0 else 0

        # Set entry details if first position
        if self.entry_timestamp is None:
            self.entry_timestamp = datetime.utcnow().isoformat()
            self.entry_prob = entry_prob or price

        # Record trade
        trade = Trade(
            timestamp=datetime.utcnow().isoformat(),
            side=side,
            shares=shares,
            price=price,
            trade_type=TradeType.BUY,
            usdc_amount=usdc_amount
        )
        self.trades.append(trade)

        self.save()

    def sell_shares(
        self,
        shares: float,
        price: float,
        side: str = PositionSide.YES,
        execute_trade: bool = False
    ) -> float:
        """
        Sell shares.

        Args:
            shares: Number of shares to sell
            price: Price per share
            side: Position side (PositionSide.YES or PositionSide.NO)
            execute_trade: If True, execute real blockchain transaction

        Returns:
            USDC proceeds from sale
        """
        from my_agent.utils.logger import log_info, log_success, log_warning

        if side == PositionSide.YES:
            if shares > self.yes_shares:
                raise ValueError(f"Cannot sell {shares} YES shares, only have {self.yes_shares}")
        else:  # NO
            if shares > self.no_shares:
                raise ValueError(f"Cannot sell {shares} NO shares, only have {self.no_shares}")

        usdc_proceeds = shares * price

        # Execute real trade if enabled
        if execute_trade and self.polymarket_client and self.token_id:
            try:
                log_info(f"🔐 Executing REAL blockchain transaction...")
                log_info(f"   SELL {shares:.2f} {side} @ ${price:.4f} = ${usdc_proceeds:.2f} USDC")

                # Execute market sell order via Polymarket
                order_result = self.polymarket_client.execute_order(
                    price=price,
                    size=shares,
                    side=TradeType.SELL,
                    token_id=self.token_id
                )

                log_success(f"✅ Transaction successful! Order ID: {order_result}")

            except Exception as e:
                log_warning(f"❌ Blockchain transaction failed: {e}")
                raise
        else:
            log_info(f"📝 DEMO MODE: Simulating SELL {shares:.2f} {side} @ ${price:.4f}")

        # Update local state
        if side == PositionSide.YES:
            self.yes_shares -= shares
        else:  # NO
            self.no_shares -= shares

        self.total_withdrawn += usdc_proceeds

        # Record trade
        trade = Trade(
            timestamp=datetime.utcnow().isoformat(),
            side=side,
            shares=shares,
            price=price,
            trade_type=TradeType.SELL,
            usdc_amount=usdc_proceeds
        )
        self.trades.append(trade)

        self.save()
        return usdc_proceeds

    def calculate_unrealized_pnl(self, yes_price: float, no_price: float) -> Dict[str, float]:
        """
        Calculate unrealized PnL.

        Args:
            yes_price: Current YES token price
            no_price: Current NO token price

        Returns:
            Dictionary with PnL metrics
        """
        # Current value of holdings
        yes_value = self.yes_shares * yes_price
        no_value = self.no_shares * no_price
        total_value = yes_value + no_value

        # Cost basis
        yes_cost = self.yes_shares * self.avg_cost_yes
        no_cost = self.no_shares * self.avg_cost_no
        total_cost = yes_cost + no_cost

        # PnL
        unrealized_pnl = total_value - total_cost

        # Net PnL (including withdrawals)
        net_pnl = (total_value + self.total_withdrawn) - self.total_invested

        return {
            "yes_value": yes_value,
            "no_value": no_value,
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "net_pnl": net_pnl,
            "roi": (net_pnl / self.total_invested * 100) if self.total_invested > 0 else 0
        }

    def calculate_locked_pnl(self, yes_price: float = 1.0, no_price: float = 1.0) -> float:
        """
        Calculate locked (guaranteed) PnL from hedged position.

        When you hold both YES and NO shares, you're guaranteed a payout
        regardless of outcome. This calculates that guaranteed profit.

        Args:
            yes_price: Final payout if YES wins (default $1)
            no_price: Final payout if NO wins (default $1)

        Returns:
            Locked profit amount
        """
        # Minimum shares across both sides
        hedged_shares = min(self.yes_shares, self.no_shares)

        if hedged_shares <= 0:
            return 0.0

        # Guaranteed payout (one side pays $1 per share)
        guaranteed_payout = hedged_shares * 1.0

        # Cost of those hedged shares
        hedged_cost_yes = hedged_shares * self.avg_cost_yes
        hedged_cost_no = hedged_shares * self.avg_cost_no
        hedged_cost = hedged_cost_yes + hedged_cost_no

        # Locked profit
        locked_pnl = guaranteed_payout - hedged_cost

        return locked_pnl

    def get_position_summary(self, yes_price: float, no_price: float) -> Dict:
        """
        Get complete position summary.

        Args:
            yes_price: Current YES price
            no_price: Current NO price

        Returns:
            Complete position metrics
        """
        unrealized = self.calculate_unrealized_pnl(yes_price, no_price)
        locked = self.calculate_locked_pnl()

        return {
            "yes_shares": self.yes_shares,
            "no_shares": self.no_shares,
            "avg_cost_yes": self.avg_cost_yes,
            "avg_cost_no": self.avg_cost_no,
            "entry_prob": self.entry_prob,
            "entry_timestamp": self.entry_timestamp,
            "total_invested": self.total_invested,
            "total_withdrawn": self.total_withdrawn,
            "current_yes_price": yes_price,
            "current_no_price": no_price,
            **unrealized,
            "locked_pnl": locked,
            "is_hedged": self.yes_shares > 0 and self.no_shares > 0,
            "num_trades": len(self.trades)
        }

    def reset(self):
        """Reset position to initial state."""
        self.yes_shares = 0.0
        self.no_shares = 0.0
        self.avg_cost_yes = 0.0
        self.avg_cost_no = 0.0
        self.entry_prob = 0.0
        self.entry_timestamp = None
        self.total_invested = 0.0
        self.total_withdrawn = 0.0
        # Keep trade history
        self.save()

    def has_position(self) -> bool:
        """Check if position is open."""
        return self.yes_shares > 0 or self.no_shares > 0

    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            "yes_shares": self.yes_shares,
            "no_shares": self.no_shares,
            "avg_cost_yes": self.avg_cost_yes,
            "avg_cost_no": self.avg_cost_no,
            "entry_prob": self.entry_prob,
            "entry_timestamp": self.entry_timestamp,
            "total_invested": self.total_invested,
            "total_withdrawn": self.total_withdrawn,
            "trades": [trade.to_dict() for trade in self.trades]
        }

    def save(self):
        """Save position to file."""
        with open(self.position_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self):
        """Load position from file."""
        if not os.path.exists(self.position_file):
            return

        with open(self.position_file, 'r') as f:
            data = json.load(f)

        self.yes_shares = data.get("yes_shares", 0.0)
        self.no_shares = data.get("no_shares", 0.0)
        self.avg_cost_yes = data.get("avg_cost_yes", 0.0)
        self.avg_cost_no = data.get("avg_cost_no", 0.0)
        self.entry_prob = data.get("entry_prob", 0.0)
        self.entry_timestamp = data.get("entry_timestamp")
        self.total_invested = data.get("total_invested", 0.0)
        self.total_withdrawn = data.get("total_withdrawn", 0.0)

        # Load trades
        self.trades = [
            Trade.from_dict(trade_data)
            for trade_data in data.get("trades", [])
        ]


# Singleton instance
_position_instance: Optional[Position] = None


def get_position(
    position_file: str = "position.json",
    polymarket_client: Optional["Polymarket"] = None,
    token_id: Optional[str] = None
) -> Position:
    """
    Get or create position singleton.

    Args:
        position_file: Path to position file
        polymarket_client: Polymarket client for blockchain transactions
        token_id: Market token ID for trading

    Returns:
        Position instance
    """
    global _position_instance
    if _position_instance is None:
        _position_instance = Position(
            position_file=position_file,
            polymarket_client=polymarket_client,
            token_id=token_id
        )
    # Update client if provided (allows re-initialization)
    elif polymarket_client is not None:
        _position_instance.polymarket_client = polymarket_client
        _position_instance.token_id = token_id
    return _position_instance
