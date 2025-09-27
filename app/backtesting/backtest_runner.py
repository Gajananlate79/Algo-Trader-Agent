import pandas as pd
import numpy as np

from app.backtesting.backtest_util import setup_logger
from app.strategy.vwap_breakout_strategy import VWAPAdvancedStrategy


class BacktestRunner:
    """
    Backtest engine for running historical simulations using VWAPAdvancedStrategy
    and OHLC data fetched from UpstoxWrapper.get_ohlc().
    """

    def __init__(self, ohlc_df: pd.DataFrame, starting_balance=100000.0):
        """
        Initialize backtest runner.

        Args:
            ohlc_df (pd.DataFrame): DataFrame with columns:
                ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            starting_balance (float): Initial capital for backtest.
        """
        self.ohlc_df = ohlc_df.copy()
        self.ohlc_df.sort_values(by="timestamp", inplace=True)  # Ensure time order

        self.starting_balance = starting_balance
        self.cash = starting_balance
        self.positions = []  # List of open trades
        self.closed_trades = []  # Completed trades
        self.logger = setup_logger()

        self.strategy = VWAPAdvancedStrategy()

    # ----------------------------------------------------------------
    # Internal Helper Functions
    # ----------------------------------------------------------------
    def _open_position(self, side, price, stop_loss, take_profit, timestamp):
        """Open a new simulated trade."""
        position = {
            "side": side,  # BUY or SELL
            "entry_price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": timestamp,
            "status": "OPEN"
        }
        self.positions.append(position)
        self.logger.info(f"Opened {side} @ {price:.2f} | SL={stop_loss:.2f} TP={take_profit:.2f}")

    def _update_positions(self, price, timestamp):
        """
        Update open positions and check if SL/TP are hit.
        """
        for pos in self.positions[:]:
            # Check Stop Loss
            if pos["side"] == "BUY" and price <= pos["stop_loss"]:
                self._close_position(pos, price, timestamp, "STOP_LOSS")
            elif pos["side"] == "SELL" and price >= pos["stop_loss"]:
                self._close_position(pos, price, timestamp, "STOP_LOSS")

            # Check Take Profit
            elif pos["side"] == "BUY" and price >= pos["take_profit"]:
                self._close_position(pos, price, timestamp, "TAKE_PROFIT")
            elif pos["side"] == "SELL" and price <= pos["take_profit"]:
                self._close_position(pos, price, timestamp, "TAKE_PROFIT")

    def _close_position(self, pos, exit_price, timestamp, reason):
        """
        Close a position and update account balance.
        """
        qty = 10  # Fixed quantity for now
        pnl = 0

        if pos["side"] == "BUY":
            pnl = (exit_price - pos["entry_price"]) * qty
        else:  # SELL
            pnl = (pos["entry_price"] - exit_price) * qty

        self.cash += pnl
        pos["status"] = "CLOSED"
        pos["exit_price"] = exit_price
        pos["exit_timestamp"] = timestamp
        pos["pnl"] = pnl
        pos["reason"] = reason

        self.closed_trades.append(pos)
        self.positions.remove(pos)

        self.logger.info(f"Closed {pos['side']} @ {exit_price:.2f} | PnL={pnl:.2f} | Reason={reason}")

    # ----------------------------------------------------------------
    # Main Backtest Loop
    # ----------------------------------------------------------------
    def run(self, symbol="SYMBOL"):
        """
        Run the backtest on the provided OHLC data.
        """
        self.logger.info(f"Starting backtest for {symbol}")
        self.logger.info(f"Initial Balance: {self.starting_balance:.2f}")

        for idx, row in self.ohlc_df.iterrows():
            timestamp = row["timestamp"]
            price = row["close"]
            volume = row["volume"]

            # Update open positions
            self._update_positions(price, timestamp)

            # Strategy evaluation
            signal_data = self.strategy.evaluate(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=timestamp
            )

            if signal_data and "signal" in signal_data:
                side = signal_data["signal"]
                stop_loss = signal_data["stop_loss"]
                take_profit = signal_data["take_profit"]

                # Open a new trade
                self._open_position(side, price, stop_loss, take_profit, timestamp)

        self._final_report()

    # ----------------------------------------------------------------
