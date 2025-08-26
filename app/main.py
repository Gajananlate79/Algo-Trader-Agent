import pandas as pd
import backtrader as bt
from datetime import time

from data.data_provider import DataProvider
from broker.upstox_wrapper import UpstoxWrapper
from utils.strategy_logger import StrategyLogger
from risk.risk_manager import RiskManager
from strategies.vwap_breakout_strategy import VWAPBreakoutStrategy


def select_top_stocks(broker, stock_list, top_n=10):
    stock_scores = {}
    for sym in stock_list:
        df = broker.get_ohlc(symbol=sym, interval="5minute", from_date="2025-01-01")
        if df.empty:
            continue
        stock_scores[sym] = df['volume'].sum()
    top_stocks = sorted(stock_scores, key=stock_scores.get, reverse=True)[:top_n]
    return top_stocks


class Main:
    def __init__(self, mock_mode=False, allow_short=True):
        self.logger = StrategyLogger()
        self.risk_manager = RiskManager(
            max_capital=100000, max_loss_per_day=5000, max_loss_per_trade=1000
        )
        self.broker = UpstoxWrapper(
            api_key="25ade58c-4dfb-464a-91d4-0fc61c145d05",
            access_token="eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGFkNWVhOTI1ODlkYjMxNTkyN2ZlMjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NjE5MjQyNSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU2MjQ1NjAwfQ.uWCeFU_mqENYFO3k38IcJ_FY9lRyNbgSyLNWqPczg1I",
            logger=self.logger,
            real_trade=False
        )
        self.mock_mode = mock_mode
        self.allow_short = allow_short

    def run(self):
        # Fetch Nifty50 list
        nifty50_stocks = DataProvider.fetch_nifty50_stocks()
        self.logger.log("info", f"Fetched {len(nifty50_stocks)} Nifty50 stocks")

        # Select top stocks by volume
        top_10 = select_top_stocks(self.broker, nifty50_stocks, top_n=10)
        self.logger.log("info", f"Top 10 stocks by volume: {top_10}")
        top_3 = top_10[:3]
        self.logger.log("info", f"Top 3 stocks for trading: {top_3}")

        # Initialize Backtrader
        cerebro = bt.Cerebro()
        for sym in top_3:
            df = self.broker.get_ohlc(symbol=sym, interval="5minute", from_date="2025-01-01")
            if not df.empty:
                # Lowercase columns
                df = df.rename(columns={c: c.lower() for c in df.columns})

                # Ensure required columns
                for col in ["open", "high", "low", "close", "volume"]:
                    if col not in df.columns:
                        df[col] = 0
                df['openinterest'] = 0

                # Convert integer timestamps to datetime
                if df['datetime'].dtype in ['int64', 'int32', 'float64']:
                    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms', errors='coerce')
                else:
                    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

                # Drop rows with invalid datetime
                df = df.dropna(subset=['datetime'])

                # Set datetime as index
                df = df.set_index('datetime')

                self.logger.log("info", f"{sym} OHLC data shape after conversion: {df.shape}")

                # Backtrader feed
                feed = bt.feeds.PandasData(dataname=df, datetime=None)
                cerebro.adddata(feed, name=sym)
            else:
                self.logger.log("warning", f"No OHLC data for {sym}, skipping")

        # Add VWAP breakout strategy
        cerebro.addstrategy(
            VWAPBreakoutStrategy,
            trade_logger=self.logger,
            broker=self.broker,
            risk_manager=self.risk_manager,
            allow_short=self.allow_short
        )

        # Run the strategy
        cerebro.run()
        self.logger.log("info", "Strategy run completed")


if __name__ == "__main__":
    # Set mock_mode=False to use live Upstox data
    app = Main(mock_mode=False, allow_short=True)
    app.run()
