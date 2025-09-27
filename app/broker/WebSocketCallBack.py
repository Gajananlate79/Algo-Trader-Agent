import logging
import time
from upstox_wrapper import UpstoxWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebSocketTest")

def main():
    access_token = (
        "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ."
        "eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGMxMThiNzQ5NTkwMjBlYjJmMGM1NjIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2Us"
        "ImlhdCI6MTc1NzQ4NTIzOSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU3NTQxNjAwfQ.iaGlSZrlszfjuqCzUkuc2hqU1UFEDay1sjDZl84MqcA"
    )

    instrument_keys = ["NSE_EQ|INE467B01029"]  # Example: ABB
    subscription_mode = "full"

    try:
        upstox = UpstoxWrapper(access_token, sandbox=True)
        logger.info("Starting WebSocket streaming with authorized URL...")
        upstox.start_streaming_not_working(instrument_keys, mode=subscription_mode)

        print("Subscribed to market data. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Closing WebSocket...")

    except Exception as e:
        logger.error(f"Error during streaming: {e}")
    finally:
        logger.info("Streaming test completed.")

if __name__ == "__main__":
    main()
