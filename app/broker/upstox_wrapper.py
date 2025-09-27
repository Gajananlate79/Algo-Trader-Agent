import json
import logging
from datetime import datetime, timedelta

import pandas as pd
import requests
import upstox_client
from upstox_client.rest import ApiException

from app.utils.logger import Logger
from app.websocket.market_data.v3.websocket_client import fetch_market_data

logging.basicConfig(level=logging.DEBUG)


class UpstoxWrapper:
    def __init__(self, access_token, mock_mode=True):
        """
        Upstox V3 Wrapper for historical OHLC, live-streaming, and order management.

        :param access_token: Live API token
        :param mock_mode: True = paper trading, False = real trades
        """

        self.access_token = access_token
        self.logger = Logger()
        self.base_url = "https://api.upstox.com/v3"
        self.mock_mode = mock_mode
        self.live_callbacks = {}
        self.ws = None
        self.connected = False

        # ✅ Initialize Upstox REST client
        # NOTE: base_url is automatically handled by the SDK
        # self.client = Upstox(api_key="2rtpqcv0kv", access_token=self.access_token)

        configuration = upstox_client.Configuration()
        access_token = self.access_token  # Replace with your actual access token
        configuration.access_token = access_token

        # 2. Instantiate the Market Data Streamer client.
        self.streamer = upstox_client.MarketDataStreamerV3(upstox_client.ApiClient(configuration))
        # 3
        self.history_api = upstox_client.HistoryV3Api(upstox_client.ApiClient(configuration))

        if self.logger:
            self.logger.log("info", f"Upstox V3 Wrapper initialized. Mock mode = {mock_mode}")

    def get_intraday_ohlc(self, instrument_keys, interval: int = 5, to_date=None, from_date=None):
        self.logger.log("info",
                        f"Fetching intraday data for {len(instrument_keys)} instruments for today {datetime.today()}"
                        f"at {interval} interval")

        # The time interval for the candles
        # self, instrument_key, unit, interval, to_date, from_date, ** kwargs)
        all_candles = {}
        for instrument_key in instrument_keys:
            try:
                ##This is intraday data for current trade day
                api_response = self.history_api.get_intra_day_candle_data(
                    instrument_key=instrument_key,
                    unit="minutes",
                    interval=interval,
                )

                if not api_response.data or not api_response.data.candles:
                    self.logger.log("warning", f"No Intraday(today) data found for {instrument_key}")
                    continue

                all_candles[instrument_key] = api_response.data.candles
                self.logger.log("info",
                                f"Successfully fetched intraday(today) {len(api_response.data.candles)} candles for {instrument_key}")

            except ApiException as e:
                self.logger.log("error", f"Exception fetching intraday(today) data for {instrument_key}: {str(e)}")

        # Convert all instruments into one combined DataFrame
        merged_df = self._convert_to_dataframe(all_candles)

        if merged_df.empty:
            self.logger.log("warning", "Current trading intraday data is not available. Check if Bot is running on non trading day or not ?")
            return merged_df

        cleaned_df = self._clean_intraday_data(merged_df)

        return cleaned_df

    def get_historical_ohlc(self, instrument_keys, interval: int = 5, to_date=None, from_date=None):
        """
        Fetch historical OHLC data for multiple instruments using Upstox Python SDK.

        :param instrument_keys: List of instrument keys (e.g., ["NSE_EQ|INE467B01029", "NSE_EQ|INE669E01016"])
        :param interval: Candle interval (e.g., "1minute", "5minute", "15minute", "day")
        :param from_date: Start datetime (YYYY-MM-DDTHH:MM:SS)
        :param to_date: End datetime (YYYY-MM-DDTHH:MM:SS)
        :return: DataFrame containing merged OHLC data
        """
        self.logger.log("info", f"Supplied from date: {from_date}")
        self.logger.log("info", f"Supplied to date: {to_date}")

        today = datetime.today()
        # Format the date as YYYY MM DD
        formatted_today_date = today.strftime("%Y-%m-%d")
        # Default: Today's full market session
        if not to_date:
            to_date = formatted_today_date
        if not from_date:
            from_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")  ##1 month

        self.logger.log("info",
                        f"Fetching historical data for {len(instrument_keys)} instruments from {from_date} to {to_date} at {interval} interval.")

        # The time interval for the candles
        # self, instrument_key, unit, interval, to_date, from_date, ** kwargs)
        all_candles = {}
        for instrument_key in instrument_keys:
            try:
                api_response = self.history_api.get_historical_candle_data1(
                    ##This is intraday data for current trade day
                    instrument_key=instrument_key,
                    unit="minutes",
                    interval=interval,
                    to_date=to_date,
                    from_date=from_date
                )

                if not api_response.data or not api_response.data.candles:
                    self.logger.log("warning", f"No historical data for {instrument_key}")
                    continue

                all_candles[instrument_key] = api_response.data.candles
                self.logger.log("info",
                                f"Successfully fetched {len(api_response.data.candles)} candles for {instrument_key}")

            except ApiException as e:
                self.logger.log("error", f"Exception fetching data for {instrument_key}: {str(e)}")

        # Convert all instruments into one combined DataFrame
        merged_df = self._convert_to_dataframe(all_candles)
        #Clean intraday data before 9:15
        return merged_df

    def _convert_to_dataframe(self, all_candles):
        """
        Helper function to convert the nested dictionary of candles into a single pandas DataFrame.
        """
        all_rows = []

        for instrument_key, candles in all_candles.items():
            for candle in candles:
                # Candle format expected: [timestamp, open, high, low, close, volume]
                all_rows.append({
                    "instrument_key": instrument_key,
                    "timestamp": candle[0],
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                    "price": candle[4]
                })

        if not all_rows:
            self.logger.log("warning", "No candles were returned for any instrument for converting to dataframe.")
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # remove all row with nan value
        self.logger.log("info", f"DataFrame created with {len(df)} rows with Nan values.")
        clean_historical_data = df.dropna()  #Drop at least one element is missing
        #Trim to last 500 bars per stock
        #clean_historical_data_tail_by_500 = (clean_historical_data.groupby("instrument_key").apply(lambda x: x.tail(500)).reset_index(drop=True))
        #self.logger.log("info", f"Final merged DataFrame created with {len(clean_historical_data_tail_by_500)} rows.")

        return clean_historical_data

    # --------------------------------------------------------
    # 2. WebSocket Streaming for Live Data
    # --------------------------------------------------
    # START STREAMING
    # --------------------------------------------------
    async def start_streaming(self, instrument_keys, mode: str, callback_func):
        """
        Start real-time market data streaming using MarketDataStreamerV3.
        :param callback_func:
        :param mode:
        :param instrument_keys: List of instrument keys like ['NSE_EQ|INE009A01021']
        :param callback_func: Function to call when new tick data is received
        """
        """
        if self.mock_mode: #keep it off. Real data should be fetched in mock mode
            self.logger.log("warning", "Mock mode enabled - skipping real streaming.")
            return
        """
        self.logger.log("info", f"Preparing to stream data for: {instrument_keys}")

        try:
            await fetch_market_data(instrument_keys=instrument_keys, mode=mode, message_handler=callback_func,
                                    access_token=self.access_token)
        except Exception as e:
            self.logger.log("error", f"Error starting streaming: {str(e)}")

    # --------------------------------------------------------
    # 3. Place Orders
    # --------------------------------------------------------
    def place_order(self, symbol, side, qty, price=None):
        """
        Place a buy/sell order via Upstox API.
        """
        self.logger.log("info", f"ORDER: {side} {qty} {symbol} @ {price or 'MARKET'}")

        url = f"{self.base_url}/order/place"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        payload = {
            "quantity": 1,
            "product": "D",
            "validity": "DAY",
            "price": 0, #Not required for market order
            "tag": "string",
            "instrument_token":symbol,
            "order_type": "MARKET",
            "transaction_type": "BUY" if side.upper() == "BUY" else "SELL",
            "disclosed_quantity": 0,
            "trigger_price": round(price, 2),
            "is_amo": False,
            "slice": True
        }




        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Order placement failed: {response.status_code} {response.text}")

        if self.logger:
            self.logger.log("info", f"ORDER PLACED: {side} {qty} {symbol}")

        return response.json()

    # --------------------------------------------------------
    # 4. Cancel Orders
    # --------------------------------------------------------
    def cancel_order(self, order_id):
        """
        Cancel an existing order.
        """
        url = f"{self.base_url}/order/cancel/{order_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.delete(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Order cancel failed: {response.status_code} {response.text}")

        if self.logger:
            self.logger.log("info", f"Order {order_id} cancelled successfully")

        return response.json()

    def _clean_intraday_data(self, current_data):

        df = current_data.dropna(subset=["open", "high", "low", "close", "price", "volume"])

        # Keep only regular session time 09:15 - 15:30
        df = df[
            (df['timestamp'].dt.time >= datetime.strptime("09:15", "%H:%M").time()) &
            (df['timestamp'].dt.time <= datetime.strptime("15:30", "%H:%M").time())
            ]
        self.logger.log("info", "Data cleaned before 9:15 am and after 15:30 {df.len}")

        return df

    def select_top_stocks_by_today_volume(self, today_df):
        """
        Select top 3 stocks based on today's intraday cumulative volume.

        historical_df must have:
        ['instrument_key', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        """


        # Filter regular market session (09:15 to 15:30)
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()

        today_df = today_df[
            (today_df['timestamp'].dt.time >= market_open) &
            (today_df['timestamp'].dt.time <= market_close)
            ]

        if today_df.empty:
            print("No trading data for today yet!")
            return []

        # Calculate cumulative volume for each instrument
        cumulative_volume = today_df.groupby("instrument_key")["volume"].sum().reset_index()

        # Sort by volume descending and pick top 3
        top_stocks = cumulative_volume.sort_values(by="volume", ascending=False).head(3)

        # Extract the instrument keys
        selected_keys = top_stocks['instrument_key'].tolist()
        self.logger.log("info", f"Selected current trading day top 3 stocks: {selected_keys} ")
        return selected_keys
