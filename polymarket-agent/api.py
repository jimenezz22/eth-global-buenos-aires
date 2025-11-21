"""
Flask API wrapper for Polymarket Hedge Agent.
Exposes trading strategy via HTTP endpoints for Hedera A2A integration.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Dict, Optional
import traceback

# Import agent components
from my_agent.position import Position
from my_agent.strategy import TradingStrategy
from my_agent.utils.config import config
from my_agent.utils.logger import log_info, log_success, log_error

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global position manager (singleton for demo)
position_manager: Optional[Position] = None
strategy: Optional[TradingStrategy] = None


def initialize_agent():
    """Initialize the agent components."""
    global position_manager, strategy

    if position_manager is None:
        # Use demo position file for API
        position_manager = Position(
            position_file="position_api.json",
            polymarket_client=None,  # No blockchain execution via API (for safety)
            token_id=None
        )

        strategy = TradingStrategy(
            position=position_manager,
            take_profit_threshold=config.TAKE_PROFIT_PROBABILITY,
            stop_loss_threshold=config.STOP_LOSS_PROBABILITY,
            hedge_sell_percent=config.HEDGE_SELL_PERCENT
        )

        log_info("✅ API agent initialized")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "polymarket-hedge-agent-api",
        "version": "1.0.0"
    })


@app.route('/position', methods=['GET'])
def get_position():
    """Get current position status."""
    initialize_agent()

    return jsonify({
        "yes_shares": position_manager.yes_shares,
        "no_shares": position_manager.no_shares,
        "total_invested": position_manager.total_invested,
        "total_withdrawn": position_manager.total_withdrawn,
        "has_position": position_manager.has_position(),
        "is_hedged": position_manager.yes_shares > 0 and position_manager.no_shares > 0,
        "entry_prob": position_manager.entry_prob,
        "avg_cost_yes": position_manager.avg_cost_yes,
        "avg_cost_no": position_manager.avg_cost_no
    })


@app.route('/bet', methods=['POST'])
def execute_bet():
    """
    Main endpoint for Hedera A2A integration.

    Request body:
    {
        "action": "evaluate" | "enter" | "hedge" | "exit",
        "amount_usd": 1000,
        "current_prob": 0.86,
        "yes_price": 0.86,
        "no_price": 0.14
    }

    Returns:
    {
        "success": true,
        "action": "HEDGE" | "HOLD" | "STOP_LOSS" | "WAIT",
        "locked_pnl_usd": 62.5,
        "message": "Hedge executed successfully",
        "position": {...}
    }
    """
    try:
        initialize_agent()

        data = request.json
        action = data.get('action', 'evaluate')
        amount_usd = data.get('amount_usd', 1000)
        current_prob = data.get('current_prob', 0.80)
        yes_price = data.get('yes_price', current_prob)
        no_price = data.get('no_price', 1 - current_prob)

        log_info(f"📨 API Request: {action} - prob={current_prob}, amount=${amount_usd}")

        # Handle different actions
        if action == 'enter':
            # Open initial position
            shares = amount_usd / yes_price
            position_manager.open_position(
                shares=shares,
                price=yes_price,
                side="YES",
                entry_prob=current_prob,
                execute_trade=False  # API never executes real trades
            )

            return jsonify({
                "success": True,
                "action": "ENTRY",
                "message": f"Opened position: {shares:.2f} YES @ ${yes_price:.4f}",
                "position": {
                    "yes_shares": position_manager.yes_shares,
                    "invested": position_manager.total_invested
                }
            })

        elif action == 'evaluate':
            # Evaluate current position and recommend action
            recommendation = strategy.evaluate(current_prob, yes_price, no_price)

            response = {
                "success": True,
                "action": recommendation["action"],
                "reason": recommendation.get("reason", ""),
                "current_prob": current_prob,
                "position": {
                    "yes_shares": position_manager.yes_shares,
                    "no_shares": position_manager.no_shares,
                    "is_hedged": position_manager.yes_shares > 0 and position_manager.no_shares > 0
                }
            }

            # Add PnL if available
            if "unrealized_pnl" in recommendation:
                response["unrealized_pnl_usd"] = recommendation["unrealized_pnl"]

            return jsonify(response)

        elif action == 'hedge':
            # Execute take-profit hedge
            if not strategy.should_take_profit(current_prob):
                return jsonify({
                    "success": False,
                    "error": f"Take-profit not triggered (prob {current_prob*100:.1f}% < {strategy.take_profit_threshold*100:.1f}%)"
                }), 400

            result = strategy.book_profit_and_rebalance(
                yes_price=yes_price,
                no_price=no_price,
                execute_trades=False  # API never executes real trades
            )

            log_success(f"✅ Hedge executed via API: Locked PnL ${result['locked_pnl']:.2f}")

            return jsonify({
                "success": True,
                "action": "HEDGE",
                "locked_pnl_usd": result['locked_pnl'],
                "message": f"Hedge executed: sold {result['yes_sold']:.0f} YES, bought {result['no_bought']:.0f} NO",
                "position": {
                    "yes_shares": position_manager.yes_shares,
                    "no_shares": position_manager.no_shares,
                    "locked_pnl": result['locked_pnl']
                },
                "trade_details": {
                    "yes_sold": result['yes_sold'],
                    "yes_price": result['yes_price'],
                    "no_bought": result['no_bought'],
                    "no_price": result['no_price'],
                    "proceeds": result['proceeds']
                }
            })

        elif action == 'exit':
            # Execute stop-loss exit
            result = strategy.cut_loss_and_exit(
                yes_price=yes_price,
                no_price=no_price,
                execute_trades=False  # API never executes real trades
            )

            return jsonify({
                "success": True,
                "action": "STOP_LOSS",
                "final_pnl_usd": result['final_pnl'],
                "message": f"Position exited: ${result['total_proceeds']:.2f} recovered",
                "trade_details": {
                    "yes_sold": result['yes_sold'],
                    "no_sold": result.get('no_sold', 0),
                    "total_proceeds": result['total_proceeds']
                }
            })

        else:
            return jsonify({
                "success": False,
                "error": f"Unknown action: {action}. Use 'enter', 'evaluate', 'hedge', or 'exit'"
            }), 400

    except Exception as e:
        log_error(f"❌ API Error: {str(e)}")
        log_error(traceback.format_exc())

        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc() if app.debug else None
        }), 500


@app.route('/reset', methods=['POST'])
def reset_position():
    """Reset position (for testing)."""
    initialize_agent()
    position_manager.reset()

    return jsonify({
        "success": True,
        "message": "Position reset successfully"
    })


if __name__ == '__main__':
    print("🚀 Starting Polymarket Hedge Agent API...")
    print("📍 Endpoints:")
    print("   GET  /health     - Health check")
    print("   GET  /position   - Get current position")
    print("   POST /bet        - Execute betting action")
    print("   POST /reset      - Reset position")
    print("\n🔗 Listening on http://localhost:5000")

    app.run(
        host='0.0.0.0',
        port=5001,  # Changed from 5000 (AirPlay on macOS)
        debug=True
    )
