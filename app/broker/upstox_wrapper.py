import pandas as pd
from upstox_api.api import Upstox

class UpstoxWrapper:
    def __init__(self, api_key, access_token, logger=None, real_trade=False):
        """
        real_trade: True = place live orders
                    False = paper trading (simulate orders)
        """
        self.api_key = api_key
        self.access_token = access_token
        self.logger = logger
        self.real_trade = real_trade
        self.upstox = Upstox(self.api_key, self.access_token)

    def get_ohlc(self, symbol, interval="5minute", from_date=None):
        """
        Fetch live OHLC data from Upstox for Backtrader.
        Works in both real and paper mode.
        """
        try:
            raw = self.upstox.get_ohlc(symbol, interval=interval, start=from_date)
            if not raw:
                if self.logger:
                    self.logger.log("warning", f"No OHLC returned for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(raw)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
            df = df.dropna(subset=['datetime'])
            df = df.rename(columns={'open':'open','high':'high','low':'low','close':'close','volume':'volume'})
            df = df[['datetime','open','high','low','close','volume']]
            df['openinterest'] = 0
            df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
            df = df.set_index('datetime').sort_index()
            return df

        except Exception as e:
            if self.logger:
                self.logger.log("error", f"Error fetching OHLC for {symbol}: {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, qty):
        """
        Place order if real_trade=True, else simulate (paper trading)
        """
        if self.real_trade:
            try:
                # Example Upstox SDK order call
                self.upstox.place_order(transaction_type=side, instrument=symbol, quantity=qty,
                                        order_type='MARKET', product='MIS')
                if self.logger:
                    self.logger.log("info", f"Live order placed: {side} {qty} {symbol}")
            except Exception as e:
                if self.logger:
                    self.logger.log("error", f"Order failed for {symbol}: {e}")
        else:
            # Paper trading: just log
            if self.logger:
                self.logger.log("info", f"Paper order simulated: {side} {qty} {symbol}")
