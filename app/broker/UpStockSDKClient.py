import upstox_client
from upstox_client.rest import ApiException

configuration = upstox_client.Configuration()
configuration.access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGI4M2YxZjE2OWU2MjE3MGFjMTUyMWUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NjkwNTI0NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU2OTM2ODAwfQ.WzYcU7c9xaMhMGjOwOIWFSc_LS14cjHUq_DoPZzsZJ0'

apiInstance = upstox_client.MarketQuoteV3Api(upstox_client.ApiClient(configuration))
try:
    # For a single instrument
    response = apiInstance.get("I1", instrument_key="NSE_EQ|INE669E01016")
    print(response)
except ApiException as e:
    print("Exception when calling MarketQuoteV3Api->get_market_quote_ohlc: %s\n" % e)

##Order flow started here
body = upstox_client.PlaceOrderV3Request(
        quantity=1,
        product="D",  # "D" for Delivery, "I" for Intraday, "CO" for Cover Order, "MTF" for Margin Trading Facility
        validity="IOC",  # "DAY" for Day order
        price=9.12,  # Required for LIMIT orders
        tag="my_order_tag",  # Optional: A unique identifier for your order
        instrument_token="NSE_EQ|INE669E01016",  # Replace with the correct instrument token
        order_type="LIMIT",  # "MARKET", "LIMIT", "SL", "SL-M"
        transaction_type="BUY",  # "BUY" or "SELL"
        disclosed_quantity=0,  # Optional: Disclosed quantity
        trigger_price=0.0,  # Required for SL/SL-M orders
        is_amo=False,  # True for After Market Orders
        slice=False  # Used for multi-leg orders (advanced)
    )


configuration = upstox_client.Configuration(
    # Set to True for sandbox environment, False for production
    sandbox=True
)
configuration.access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGI4M2YxZjE2OWU2MjE3MGFjMTUyMWUiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NjkwNTI0NywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU2OTM2ODAwfQ.WzYcU7c9xaMhMGjOwOIWFSc_LS14cjHUq_DoPZzsZJ0'  # Replace with your actual access token

api_client = upstox_client.ApiClient(configuration)
api_instance = upstox_client.OrderApiV3(api_client)

try:
    api_response = api_instance.place_order(body)
   # api_response1 = api_instance.get_gtt_order_details(gtt_order_id=-250903000524065")
    print(api_response)
except ApiException as e:
    print(f"Exception when calling OrderApiV3->place_order: {e}")