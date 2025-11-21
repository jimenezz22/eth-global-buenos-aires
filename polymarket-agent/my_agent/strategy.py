"""Core trading strategy logic for automated hedging."""

from typing import Optional, Dict, Tuple

from my_agent.position import Position
from my_agent.pnl_calculator import calculate_hedge_shares
from my_agent.utils.config import config
from my_agent.utils.constants import ActionType, PositionSide
from my_agent.utils.logger import log_info, log_success, log_warning, log_error


# Global flag to control trade execution (set from config.DEMO_MODE)
EXECUTE_REAL_TRADES = not config.DEMO_MODE


class TradingStrategy:
    """Implements automated take-profit and stop-loss strategy with hedging."""

    def __init__(
        self,
        position: Position,
        take_profit_threshold: Optional[float] = None,
        stop_loss_threshold: Optional[float] = None,
        hedge_sell_percent: Optional[float] = None
    ):
        """
        Initialize trading strategy.

        Args:
            position: Position instance to manage
            take_profit_threshold: Probability to trigger take-profit (default from config)
            stop_loss_threshold: Probability to trigger stop-loss (default from config)
            hedge_sell_percent: Percentage of YES to sell when hedging (default from config)
        """
        self.position = position
        self.take_profit_threshold = take_profit_threshold or config.TAKE_PROFIT_PROBABILITY
        self.stop_loss_threshold = stop_loss_threshold or config.STOP_LOSS_PROBABILITY
        self.hedge_sell_percent = hedge_sell_percent or config.HEDGE_SELL_PERCENT

    def should_take_profit(self, current_prob: float) -> bool:
        """
        Check if should trigger take-profit.

        Args:
            current_prob: Current YES probability (0.0-1.0)

        Returns:
            True if should take profit
        """
        # Only take profit if we have YES shares
        if self.position.yes_shares <= 0:
            return False

        # Only take profit if not already hedged
        if self.position.no_shares > 0:
            return False

        # Check threshold
        return current_prob >= self.take_profit_threshold

    def should_cut_loss(self, current_prob: float) -> bool:
        """
        Check if should trigger stop-loss.

        Args:
            current_prob: Current YES probability (0.0-1.0)

        Returns:
            True if should cut losses
        """
        # Only cut loss if we have YES shares and no hedge
        if self.position.yes_shares <= 0:
            return False

        # Don't stop-loss if already hedged (profit is locked)
        if self.position.no_shares > 0:
            return False

        # Check threshold
        return current_prob <= self.stop_loss_threshold

    def book_profit_and_rebalance(
        self,
        yes_price: float,
        no_price: float,
        execute_trades: bool = True
    ) -> Dict:
        """
        Execute take-profit and hedge strategy.

        This is the core hedging logic:
        1. Sell X% of YES shares
        2. Use proceeds to buy maximum NO shares
        3. Result: Profit locked regardless of outcome

        Args:
            yes_price: Current YES price
            no_price: Current NO price
            execute_trades: If True, execute trades. If False, dry-run simulation.

        Returns:
            Dictionary with trade details
        """
        if self.position.yes_shares <= 0:
            raise ValueError("No YES shares to sell")

        # Calculate trade amounts
        yes_to_sell, no_to_buy, usdc_proceeds = calculate_hedge_shares(
            yes_shares=self.position.yes_shares,
            sell_percentage=self.hedge_sell_percent,
            yes_sell_price=yes_price,
            no_buy_price=no_price
        )

        log_info(f"Take Profit Strategy:")
        log_info(f"  Current prob: {yes_price * 100:.2f}%")
        log_info(f"  Sell {yes_to_sell:.0f} YES @ ${yes_price:.4f} → ${usdc_proceeds:,.2f}")
        log_info(f"  Buy {no_to_buy:.0f} NO @ ${no_price:.4f}")

        # Always execute locally (blockchain execution controlled by execute_trade parameter)
        # Execute sell YES (will use blockchain if execute_trades=True AND client configured)
        actual_proceeds = self.position.sell_shares(
            shares=yes_to_sell,
            price=yes_price,
            side=PositionSide.YES,
            execute_trade=execute_trades
        )

        # Execute buy NO (will use blockchain if execute_trades=True AND client configured)
        self.position.open_position(
            shares=no_to_buy,
            price=no_price,
            side=PositionSide.NO,
            execute_trade=execute_trades
        )

        # Calculate locked PnL
        locked_pnl = self.position.calculate_locked_pnl()

        log_success(f"Hedge executed! Locked PnL: ${locked_pnl:,.2f}")

        return {
            "action": ActionType.HEDGE,
            "yes_sold": yes_to_sell,
            "yes_price": yes_price,
            "no_bought": no_to_buy,
            "no_price": no_price,
            "proceeds": actual_proceeds,
            "locked_pnl": locked_pnl,
            "remaining_yes": self.position.yes_shares,
            "remaining_no": self.position.no_shares
        }

    def cut_loss_and_exit(
        self,
        yes_price: float,
        no_price: Optional[float] = None,
        execute_trades: bool = True
    ) -> Dict:
        """
        Execute stop-loss: sell all positions.

        Args:
            yes_price: Current YES price
            no_price: Current NO price (if we have NO shares to sell)
            execute_trades: If True, execute trades. If False, dry-run simulation.

        Returns:
            Dictionary with trade details
        """
        yes_shares = self.position.yes_shares
        no_shares = self.position.no_shares

        if yes_shares <= 0 and no_shares <= 0:
            raise ValueError("No position to exit")

        total_proceeds = 0.0

        log_warning(f"Stop Loss Triggered:")
        log_warning(f"  Current prob: {yes_price * 100:.2f}%")

        # Always execute locally (blockchain execution controlled by execute_trade parameter)
        # Sell all YES if we have any (will use blockchain if execute_trades=True AND client configured)
        if yes_shares > 0:
            yes_proceeds = self.position.sell_shares(
                shares=yes_shares,
                price=yes_price,
                side=PositionSide.YES,
                execute_trade=execute_trades
            )
            total_proceeds += yes_proceeds
            log_info(f"  Sold {yes_shares:.0f} YES @ ${yes_price:.4f} → ${yes_proceeds:,.2f}")

        # Sell all NO if we have any (will use blockchain if execute_trades=True AND client configured)
        if no_shares > 0 and no_price:
            no_proceeds = self.position.sell_shares(
                shares=no_shares,
                price=no_price,
                side=PositionSide.NO,
                execute_trade=execute_trades
            )
            total_proceeds += no_proceeds
            log_info(f"  Sold {no_shares:.0f} NO @ ${no_price:.4f} → ${no_proceeds:,.2f}")

        # Calculate final PnL
        final_pnl = self.position.total_withdrawn - self.position.total_invested

        if final_pnl >= 0:
            log_success(f"Exited with profit: ${final_pnl:,.2f}")
        else:
            log_error(f"Exited with loss: ${final_pnl:,.2f}")

        # Reset position
        self.position.reset()

        return {
            "action": ActionType.STOP_LOSS,
            "yes_sold": yes_shares,
            "yes_price": yes_price,
            "no_sold": no_shares,
            "no_price": no_price,
            "total_proceeds": total_proceeds,
            "final_pnl": final_pnl
        }

    def evaluate(self, current_prob: float, yes_price: float, no_price: float) -> Dict:
        """
        Evaluate current market conditions and determine action.

        Args:
            current_prob: Current YES probability
            yes_price: Current YES price
            no_price: Current NO price

        Returns:
            Dictionary with recommended action and details
        """
        # Check if we have a position
        if not self.position.has_position():
            return {
                "action": ActionType.WAIT,
                "reason": "No position open",
                "current_prob": current_prob
            }

        # Check take profit
        if self.should_take_profit(current_prob):
            return {
                "action": ActionType.TAKE_PROFIT,
                "reason": f"Probability {current_prob * 100:.1f}% >= {self.take_profit_threshold * 100:.1f}%",
                "current_prob": current_prob,
                "yes_price": yes_price,
                "no_price": no_price
            }

        # Check stop loss
        if self.should_cut_loss(current_prob):
            return {
                "action": ActionType.STOP_LOSS,
                "reason": f"Probability {current_prob * 100:.1f}% <= {self.stop_loss_threshold * 100:.1f}%",
                "current_prob": current_prob,
                "yes_price": yes_price,
                "no_price": no_price
            }

        # Hold
        pnl = self.position.calculate_unrealized_pnl(yes_price, no_price)

        return {
            "action": ActionType.HOLD,
            "reason": f"Within thresholds ({self.stop_loss_threshold * 100:.1f}% - {self.take_profit_threshold * 100:.1f}%)",
            "current_prob": current_prob,
            "unrealized_pnl": pnl["unrealized_pnl"],
            "is_hedged": self.position.yes_shares > 0 and self.position.no_shares > 0
        }

    def execute_action(self, action: Dict) -> Optional[Dict]:
        """
        Execute recommended action.

        Args:
            action: Action dictionary from evaluate()

        Returns:
            Execution result or None if no action taken
        """
        action_type = action["action"]

        if action_type == ActionType.TAKE_PROFIT:
            return self.book_profit_and_rebalance(
                yes_price=action["yes_price"],
                no_price=action["no_price"],
                execute_trades=EXECUTE_REAL_TRADES  # Respects DEMO_MODE
            )

        elif action_type == ActionType.STOP_LOSS:
            return self.cut_loss_and_exit(
                yes_price=action["yes_price"],
                no_price=action["no_price"],
                execute_trades=EXECUTE_REAL_TRADES  # Respects DEMO_MODE
            )

        elif action_type == ActionType.HOLD:
            log_info(f"HOLD - {action['reason']}")
            return None

        elif action_type == ActionType.WAIT:
            log_info(f"WAIT - {action['reason']}")
            return None

        else:
            log_warning(f"Unknown action: {action_type}")
            return None


def create_strategy(
    position: Position,
    take_profit_threshold: Optional[float] = None,
    stop_loss_threshold: Optional[float] = None,
    hedge_sell_percent: Optional[float] = None
) -> TradingStrategy:
    """
    Create a trading strategy instance.

    Args:
        position: Position instance
        take_profit_threshold: Custom take-profit threshold
        stop_loss_threshold: Custom stop-loss threshold
        hedge_sell_percent: Custom hedge sell percentage

    Returns:
        TradingStrategy instance
    """
    return TradingStrategy(
        position=position,
        take_profit_threshold=take_profit_threshold,
        stop_loss_threshold=stop_loss_threshold,
        hedge_sell_percent=hedge_sell_percent
    )
