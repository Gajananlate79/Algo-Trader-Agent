# main_backtest.py
from app.backtesting.backtest_runner import BacktestRunner
from app.broker.upstox_wrapper import UpstoxWrapper
from app.utils.logger import Logger

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGJkNjZlYWYxMWQxNTMyNGNiYzgwZmUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NzI0MzExNCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU3MjgyNDAwfQ.xzLCJNcH4hYj764Ae2qB5cp9OZg6bLHJosbhGXRCDqY"

def main():
    # Initialize wrapper
    logger = Logger(log_file="logs/trading.log")
    broker = UpstoxWrapper(access_token=ACCESS_TOKEN, logger = logger,  mock_mode= False)

    # Fetch OHLC data directly from Upstox
    ohlc_df = broker.get_intraday_ohlc(
        instrument_keys=["NSE_EQ|INE467B01029"],  # Example Reliance
        interval= 1,  # 5-minute candles
        to_date="2025-09-05",
        from_date="2025-09-05",
    )
    print(ohlc_df)
    # Run backtest
    backtest = BacktestRunner(ohlc_df)
    backtest.run(symbol="RELIANCE")

if __name__ == "__main__":
    main()
