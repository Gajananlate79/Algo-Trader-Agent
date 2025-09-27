import logging
from upstox_client.feeder.market_data_feeder_v3 import MarketDataFeederV3

logger = logging.getLogger("CustomMarketDataStreamer")

class CustomMarketDataStreamer(MarketDataFeederV3):
    """
    Extension of MarketDataFeederV3 to register custom event handlers
    like on_open, on_message, on_error, and on_close.
    """

    def __init__(self, api_client, access_token, enable_auto_reconnect=True):
        super().__init__(api_client=api_client, enable_auto_reconnect=enable_auto_reconnect)
        self.access_token = access_token
        self._custom_handlers_registered = False

    def register_handlers(self, on_open=None, on_message=None, on_error=None, on_close=None):
        """
        Register custom event handlers into the listeners dict.
        """
        if on_open:
            self.listeners['open'].append(on_open)
            logger.info("Custom on_open handler registered.")

        if on_message:
            self.listeners['message'].append(on_message)
            logger.info("Custom on_message handler registered.")

        if on_error:
            self.listeners['error'].append(on_error)
            logger.info("Custom on_error handler registered.")

        if on_close:
            self.listeners['close'].append(on_close)
            logger.info("Custom on_close handler registered.")

        self._custom_handlers_registered = True
        logger.info(f"Handlers after registration: {self.listeners}")

    def connect_and_subscribe(self, instrument_keys, mode="full"):
        """
        Connect to the websocket and subscribe to instruments in a single call.
        """
        if not self._custom_handlers_registered:
            raise RuntimeError("No handlers registered. Call register_handlers() first.")

        logger.info("Connecting to Upstox Market Data Stream...")
        self.connect()  # This opens the WebSocket connection
        logger.info("WebSocket connected. Subscribing to instruments...")

        # Subscribe to given instruments
        self.subscribe(mode=mode, instrumentKeys=instrument_keys)
        logger.info(f"Subscribed to instruments: {instrument_keys}")
