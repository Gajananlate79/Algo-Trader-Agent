import asyncio
import time
from datetime import datetime, timezone
import pandas as pd

from broker.upstox_wrapper import UpstoxWrapper
from strategy.vwap_breakout_strategy import VWAPAdvancedStrategy
from trading.paper_trading import PaperTrader
from utils.logger import Logger


class TradingBotMain:
    """
    Main trading bot class to run VWAP strategy on Nifty50 stocks
    using Upstox Python SDK v3.
    """

    def __init__(self, config):
        # Initialize logger
        self.df_instruments = None
        self.logger = Logger(log_file="logs/trading.log")

        # Config parameters
        self.config = config
        self.mock_mode = False #config.get("MOCK_MODE", False)
        self.access_token = config.get("ACCESS_TOKEN")
        self.selected_top_stock_keys = []
        # Upstox wrapper initialization
        self.broker = UpstoxWrapper(
            access_token=self.access_token,
            mock_mode=self.mock_mode
        )

        # Strategy & Paper Trading
        self.strategy = VWAPAdvancedStrategy()
        self.paper_trader = PaperTrader()
        self.placed_orders = {}  # instrument_key: order_details or True
        self.instrument_data = {}

    # --------------------------------------------------------------
    # Load Nifty50 Instrument Keys
    # --------------------------------------------------------------
    def load_nifty50_list(self, excel_path="data/nifty50.xlsx"):
        """
        Load Nifty50 instrument list from an Excel file and ensure all
        instrument keys have the required 'NSE_EQ|' prefix.

        Excel File Columns Required:
        - INSTRUMENT_KEY: Raw instrument identifier (e.g., INE467B01029)
        - SYMBOL: Human-readable stock symbol (e.g., RELIANCE)

        Returns:
            pd.DataFrame: DataFrame with clean 'INSTRUMENT_KEY' and 'SYMBOL'
        """

        try:
            # Load Excel file
            df = pd.read_excel(excel_path)

            # Validate required columns
            required_cols = {"INSTRUMENT_KEY", "SYMBOL"}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

            # Remove invalid rows
            df.dropna(subset=["INSTRUMENT_KEY", "SYMBOL"], inplace=True)

            if df.empty:
                raise ValueError("Excel file is empty or all rows are invalid")

            # Ensure every instrument key starts with NSE_EQ|
            df["INSTRUMENT_KEY"] = df["INSTRUMENT_KEY"].apply(
                lambda x: str(x).strip() if str(x).startswith("NSE_EQ|") else f"NSE_EQ|{str(x).strip()}"
            )

            # Log success
            self.logger.log("info", f"Loaded {len(df)} instruments from {excel_path} with NSE_EQ| prefix added")

            return df

        except FileNotFoundError:
            self.logger.log("error", f"Excel file not found: {excel_path}")
            return pd.DataFrame(columns=["INSTRUMENT_KEY", "SYMBOL"])
        except Exception as e:
            self.logger.log("error", f"Error loading Nifty50 list: {str(e)}")
            return pd.DataFrame(columns=["INSTRUMENT_KEY", "SYMBOL"])

    def select_top_stocks(self, df_instruments):
                """
                Fetch historical data and select top 3 stocks based on the last candle volume.

                Returns:
                    dict: {instrument_key: historical_dataframe}
                """
                self.logger.log("info", "Fetching historical data to select top 3 stocks...")

                # Extract instrument keys
                instrument_keys = df_instruments["INSTRUMENT_KEY"].tolist()
                self.logger.log("info", f"Found {len(instrument_keys)} instruments to analyze.")

                # Fetch historical OHLC data for all instruments in one call
                historical_df = self.broker.get_historical_ohlc(instrument_keys, interval=5)
                # Fetch Current day OHLC data for all instruments in one call
                current_df = self.broker.get_intraday_ohlc(instrument_keys, interval=5)

                if current_df.empty :
                    self.logger.log("error", "No current data found for stock selection!...")
                    return {}

                self.logger.log("info", f"Found OHLC data for current trading day: {current_df.size}")

                # Calculate cumulative volume for each instrument
                cumulative_volume = current_df.groupby("instrument_key")["volume"].sum().reset_index()

                # Sort by volume descending and pick top 3 stocks form today's data
                top_stocks = cumulative_volume.sort_values(by="volume", ascending=False).head(3)

                self.selected_top_stock_keys = top_stocks['instrument_key'].tolist()

                for key in self.selected_top_stock_keys:
                    symbol_row = self.df_instruments[self.df_instruments['INSTRUMENT_KEY'] == key]
                    if not symbol_row.empty:
                        symbol_value = symbol_row.iloc[0]["SYMBOL"]
                        self.logger.log("info", f"Selected top 3 stocks: {key} - {symbol_value}")

                combined_df = pd.concat([historical_df, current_df])
                combined_sorted_df = combined_df.sort_values("timestamp", ascending=False)

                # Create a dictionary mapping each selected stock to its full historical data
                historical_dict = {
                    key: combined_sorted_df[combined_sorted_df['instrument_key'] == key].copy()
                    for key in self.selected_top_stock_keys
                }

                # Log each stock's row count for debugging
                for key, df in combined_sorted_df.items():
                    self.logger.log("info", f"Historical data for {key}: {len(df)} rows loaded.")

                return historical_dict


    # --s------------------------------------------------------------
    # Run Main Trading Bot
    # --------------------------------------------------------------
    def run(self):
        """
        Main workflow:
        1. Load Nifty50 list from Excel
        2. Select top 3 stocks by volume
        3. Start streaming live data
        4. Run VWAP breakout strategy and place orders
        """
        self.logger.log("info", "Starting Trading Bot...")

        # Step 1: Load Nifty50
        self.df_instruments = self.load_nifty50_list()
        if self.df_instruments.empty:
            self.logger.log("error", "Nifty50 instrument list is empty. Exiting.")
            return

        # Step 2: Select top 3 stocks
        top_stocks_data = self.select_top_stocks(self.df_instruments)
        if not top_stocks_data:
            self.logger.log("error", "Could not select top 3 stocks. Exiting.")
            return

        for key, df in top_stocks_data.items():
            self.logger.log("info", f"Historical data for {key}: {len(df)} rows loaded.")
            self.strategy.preload_historical_data(key, df)

        self.logger.log("info", f"Strategy preloaded with historical data {self.strategy.data}")

        # Step 3: Define callback for live ticks
        def on_tick(data):
            self.logger.log("info", "on_tick Callback is called...")
            if data is None:
                print("Received None data in update_data")
                return

            try:
                symbol_key = data.get("instrument_key")
                price = data.get("ltp")  # last traded price
                volume = data.get("volume", 0)
                timestamp = convert_ltt_to_datetime(data.get("timestamp"))

                if not symbol_key or price is None:
                    return

                self.logger.log("info", f"TICK in on_tick: {symbol_key} | Price: {price} | Volume: {volume} | TimeStamp: {timestamp}")

                # Run VWAP breakout strategy
                evaluate_result = self.strategy.evaluate(symbol_key, price, volume, timestamp)
                if evaluate_result is None:
                 return

                signal = evaluate_result["signal"]

                self.mock_mode =True
                # Check if order already placed
                if self.placed_orders.get(symbol_key):
                    self.logger.log("info", f"Order already placed for {symbol_key}, skipping.")
                    return

            # add order for check
                if signal in ("BUY", "SELL"):
                    symbol_row = self.df_instruments[self.df_instruments["INSTRUMENT_KEY"] == symbol_key]
                    if not symbol_row.empty:
                        symbol_value = symbol_row.iloc[0]["SYMBOL"]
                        self.logger.log("info", f"Placing order for instrument {symbol_key} key and name {symbol_value} "
                                            f"with parameters {evaluate_result}")
                    else:
                        self.logger.log("warning", f"Symbol not found for {symbol_key}")

                self.logger.log("info", f"Placing order for instrument"
                                            f"with parameters: {evaluate_result} ")
                # Execute signals
                if signal == "BUY":
                    self.logger.log("info", f"BUY signal for {symbol_key} at {price}")
                    if self.mock_mode:
                        # Use take_profit and stop_loss from evaluate_result
                        self.paper_trader.open_position(
                            symbol_key, "BUY", price,
                            evaluate_result["stop_loss"],
                            evaluate_result["take_profit"], 10
                        )
                        self.placed_orders[symbol_key] = evaluate_result
                    else:
                        self.broker.place_order(symbol_key, "BUY", 10, price)
                        self.placed_orders[symbol_key] = evaluate_result

                elif signal == "SELL":
                    self.logger.log("info", f"SELL signal for {symbol_key} at {price}")
                    if self.mock_mode:
                        self.paper_trader.open_position(
                            symbol_key, "SELL", price,
                            evaluate_result["stop_loss"],
                            evaluate_result["take_profit"], 10
                        )
                        self.placed_orders[symbol_key] = evaluate_result
                    else:
                        self.broker.place_order(symbol_key, "SELL", 10, price)
                        self.placed_orders[symbol_key] = evaluate_result
                # Always check for SL/TP on every tick
                if self.mock_mode:
                    self.paper_trader.on_tick(symbol_key, price)

            except Exception as e:
                self.logger.log("error", f"Error processing tick: {str(e)}")

        # Step 4: Start streaming
        self.logger.log("info", "Connecting to live market data stream...")
        asyncio.run(self.broker.start_streaming(self.selected_top_stock_keys, mode="full", callback_func=on_tick))

        # Keep the bot running

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.log("warning", "Trading Bot stopped manually.")




def convert_ltt_to_datetime(ltt_value):
    """
    Convert LTT (Last Traded Time) from milliseconds to human-readable timestamp.
    """
    try:
        # LTT comes as string, so convert to int
        ltt_ms = int(ltt_value)

        # Convert to seconds
        ltt_seconds = ltt_ms / 1000.0

        # Convert to UTC datetime
        return datetime.fromtimestamp(ltt_seconds, tz=timezone.utc)
    except (ValueError, TypeError):
        return None

# --------------------------------------------------------------
# Entry Point
# --------------------------------------------------------------

if __name__ == "__main__":
    config = {
        "ACCESS_TOKEN": "add acceess token here",
        "MOCK_MODE": False  # False = Live Trading, True = Paper Trading
    }
    bot = TradingBotMain(config)
    bot.run()
