import pandas as pd

from app.utils.logger import Logger

MIN_STOP_LOSS = 0.5  # minimum ATR multiplier for SL
MIN_TAKE_PROFIT = 1.0  # minimum ATR multiplier for TP
#SHORT MA:14,LONG MA:30,RSI:14,ATR:14,RISK REWARD RATIO:2 - more stable trading. 9 and 21 for

class VWAPAdvancedStrategy:
    def __init__(self, rsi_period=14, short_ma=9, long_ma=30, atr_period=14, risk_reward_ratio=2):
        """
        Initializes strategy parameters and data storage.
        """
        self.data = {}  # symbol -> dataframe
        self.rsi_period = rsi_period
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.atr_period = atr_period
        self.risk_reward_ratio = risk_reward_ratio
        self.logger = Logger()


    # ------------------------------------------------
    # 1. LOAD HISTORICAL DATA
    # ------------------------------------------------
    def preload_historical_data(self, symbol, historical_data):
        """
        Preload historical OHLC data for a symbol before market opens.
        `historical_data` should be a list of dicts or a DataFrame with:
        timestamp, open, high, low, close, volume
        """
        #historical_data = historical_data[["timestamp", "price", "volume"]].tail(500)  # keep last 500 rows
        self.data[symbol] = historical_data
        self.logger.log("info", f"[INFO] preload_historical_data method Preloaded {len(historical_data)} rows of historical data for {symbol}")

    # ------------------------------------------------
    # 2. UPDATE WITH REAL-TIME WEBSOCKET TICKS
    # ------------------------------------------------
    def update_data(self, symbol, price, volume, timestamp, open_price=None, high=None, low=None, close=None):
        """
        Store incoming tick/candle data for calculations in real-time.
        """
        # Always use a consistent set of columns
        columns = ["timestamp", "open", "high", "low", "close", "price", "volume"]
        if symbol not in self.data:
            self.data[symbol] = pd.DataFrame(columns=columns)
        new_row = pd.DataFrame([{ #For now
            "timestamp": timestamp,
            "open": open_price if open_price is not None else price,
            "high": high if high is not None else price,
            "low": low if low is not None else price,
            "close": close if close is not None else price,
            "price": price,
            "volume": volume
        }])
        self.data[symbol] = pd.concat([self.data[symbol], new_row], ignore_index=True)
        self.data[symbol]["timestamp"] = pd.to_datetime(self.data[symbol]["timestamp"], utc=True).dt.tz_convert("UTC")
        self.data[symbol] = self.data[symbol].sort_values("timestamp").reset_index(drop=True)

        self.logger.log("info", f"In update_data method new data with old data for  {symbol} and  { self.data[symbol]}")

    # ------------------------------------------------
    # 3. METHODS FOR INDICATOR CALCULATIONS
    # ------------------------------------------------
    def calculate_vwap(self, df):
        # Use 'close' if available, else fallback to 'price'
        price_col = 'close' if 'close' in df.columns else 'price'
        df = df.copy()
        df["cum_price_vol"] = (df[price_col] * df["volume"]).cumsum()
        df["cum_vol"] = df["volume"].cumsum()
        df["vwap"] = df["cum_price_vol"] / df["cum_vol"]
        return df["vwap"].iloc[-1]

    def calculate_rsi(self, df):
        df = df.copy()
        df["delta"] = df["price"].diff()
        gain = df["delta"].clip(lower=0)
        loss = -df["delta"].clip(upper=0)

        # Wilder's smoothing (EMA)
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period, adjust=False).mean()

        rs = avg_gain / (avg_loss + 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))
        return df["rsi"].iloc[-1]

    def calculate_ma(self, df):
        """Moving Average Crossover"""
        df["ma_short"] = df["price"].rolling(window=self.short_ma).mean()
        df["ma_long"] = df["price"].rolling(window=self.long_ma).mean()
        return df["ma_short"].iloc[-1], df["ma_long"].iloc[-1]

    def calculate_atr(self, df):
        # Use OHLC if available, else fallback to price
        if all(col in df.columns for col in ['high', 'low', 'close']):
            high = df['high']
            low = df['low']
            close = df['close']
        else:
            high = low = close = df['price']
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_period).mean()
        return atr.iloc[-1]

    # ------------------------------------------------
    # 4. STRATEGY SIGNAL EVALUATION
    # ------------------------------------------------
    def evaluate(self, symbol, price, volume, timestamp):
        """
        Main signal generation:
        1. VWAP breakout as core trigger
        2. Confirm with RSI, MA
        3. Use ATR to set dynamic stop-loss and take-profit
        """

        # Update with live tick
        self.update_data(symbol, price, volume, timestamp)
        df = self.data[symbol]
        if len(df) < max(self.long_ma, self.rsi_period, self.atr_period):
            return None
        #Sort dataframe by timestamp to ensure correct order -old data should come first
        df = df.sort_values("timestamp").reset_index(drop=True)
        vwap = self.calculate_vwap(df)
        rsi = self.calculate_rsi(df)
        ma_short, ma_long = self.calculate_ma(df)
        atr = self.calculate_atr(df)
        self.logger.log("info", f"Indicators for {symbol} at {timestamp} - VWAP: {vwap}, RSI: {rsi}, MA Short: {ma_short}, MA Long: {ma_long}, ATR: {atr}")

        # Check for NaN
        if any(pd.isna(x) for x in [vwap, rsi, ma_short, ma_long, atr]):
            return None
        breakout_up = price > vwap * 1.002
        breakout_down = price < vwap * 0.998  # Fixed
        self.logger.log("info", f"Breakout conditions - Up: {breakout_up}, Down: {breakout_down}")

        # RSI filter
        rsi_overbought = rsi > 70
        rsi_oversold = rsi < 30
        self.logger.log("info", f"RSI conditions - Overbought: {rsi_overbought}, Oversold: {rsi_oversold}")

        # Trend confirmation
        uptrend = ma_short > ma_long
        downtrend = ma_short < ma_long
        self.logger.log("info", f"Trend conditions - Uptrend: {uptrend}, Downtrend: {downtrend}")

        # ATR-based risk management
        stop_loss=max(atr, MIN_STOP_LOSS)
        take_profit=max(atr * self.risk_reward_ratio, MIN_TAKE_PROFIT)
        self.logger.log("info", f"Risk Management - Stop Loss: {stop_loss}, Take Profit: {take_profit}")

        # Final Signal Logic
        if breakout_up and uptrend and not rsi_overbought:
            self.logger.log("info", f"Generating buy signal for instrument {symbol} for price { price }")
            signal_data = {
                "signal": "BUY",
                "take_profit": round(price + take_profit, 2),
                "stop_loss": round(price - stop_loss, 2),
                "vwap": round(vwap, 2),
                "rsi": round(rsi, 2),
                "price": round(price, 2)
            }
            self.logger.log("info", f"Buy signal data: {signal_data}")
            return signal_data

        elif breakout_down and downtrend and not rsi_oversold:
            self.logger.log("info",f"Generating sell signal for instrument {symbol}")
            return {
                "signal": "SELL",
                "take_profit": round(price - take_profit, 2),
                "stop_loss": round(price + stop_loss, 2),
                "vwap": round(vwap, 2),
                "rsi": round(rsi, 2),
                "price": round(price, 2)
            }

        self.logger.log("info", "No signal is generated by strategy. Please check")
        return None
