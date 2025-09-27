from app.utils.logger import Logger

from app.broker.upstox_wrapper import UpstoxWrapper

logger = Logger()

access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGJiZDFmOGIzYzFlMjEzNDBjYjdmMWYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NzEzOTQ0OCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU3MTk2MDAwfQ.JVlfkVJI-3NcD-rpEI3TwmbIh041owa02u20SExQ704"
upstox_wrapper = UpstoxWrapper(access_token=access_token)

instrument_keys = [
    "NSE_EQ|INE467B01029",  # Example instrument
    "NSE_EQ|INE669E01016"
]

df = upstox_wrapper.get_intraday_ohlc(
    instrument_keys=instrument_keys,
    interval=5,

)

print(df.head())
