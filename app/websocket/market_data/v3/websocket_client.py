# Import necessary modules
import asyncio
import json
import ssl

import uuid
import websockets
import requests
from google.protobuf.json_format import MessageToDict

import app.websocket.market_data.v3.MarketDataFeedV3_pb2 as pb




def get_market_data_feed_authorize_v3(access_token: str):
    """Get authorization for market data feed."""
    access_token = access_token
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    url = 'https://api.upstox.com/v3/feed/market-data-feed/authorize'
    api_response = requests.get(url=url, headers=headers)
    json_response = api_response.json()
    print(json_response["data"]["authorized_redirect_uri"])
    return json_response


def decode_protobuf(buffer):
    """Decode protobuf message."""
    feed_response = pb.FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response


async def fetch_market_data(instrument_keys, mode="full", message_handler = None, access_token = None):
    """Fetch market data using WebSocket and print it."""

    # Create default SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Get market data feed authorization
    response = get_market_data_feed_authorize_v3(access_token)
    # Connect to the WebSocket with SSL context
    async with websockets.connect(response["data"]["authorized_redirect_uri"], ssl=ssl_context) as websocket:
        print('Connection established in websocket for ins keys', instrument_keys)
        # Generate a random UUID (Version 4)
        guid = uuid.uuid4()
        # 2. Convert the UUID to a string
        uuid_string = str(guid)

        print(f"Generated GUID: {guid}")

        await asyncio.sleep(1)  # Wait for 1 second

        # Data to be sent over the WebSocket
        data = {
            "guid": uuid_string,
            "method": "sub",
            "data": {
                "mode": mode,
                "instrumentKeys": instrument_keys
            }
        }

        # Convert data to binary and send over WebSocket
        binary_data = json.dumps(data).encode('utf-8')
        await websocket.send(binary_data)

        # Continuously receive and decode data from WebSocket
        while True:
            try:
                # Receive a message
                message = await websocket.recv()

                # --- STEP 1: Detect message type ---
                if isinstance(message, bytes):
                    # Handle Protobuf binary message
                    decoded_protobuf = decode_protobuf(message)
                    decoded_json = MessageToDict(decoded_protobuf, preserving_proto_field_name=True)
                else:
                    # Handle plain text JSON message
                    decoded_json = json.loads(message)

                # --- STEP 2: Check for message type ---
                if isinstance(decoded_json, dict) and "type" in decoded_json:
                    # Example: Market Info message
                    if decoded_json["type"] == "market_info":
                        print("Market Info Message:")
                        print(json.dumps(decoded_json, indent=2))
                        continue

                # --- STEP 3: Handle Feeds (tick data) ---
                if "feeds" in decoded_json:
                    feeds = decoded_json["feeds"]

                    for instrument_key, feed_data in feeds.items():
                        try:
                            full_feed = feed_data.get("fullFeed", {}).get("marketFF", {})

                            # Extract Last Traded Price (LTP) and Volume
                            ltpc = full_feed.get("ltpc", {})
                            ltp = ltpc.get("ltp") #
                            ltt = ltpc.get("ltt")
                            #Get cumulative volume
                            cumulative_volume = None
                            cumulative_volume_candles = full_feed.get("marketOHLC", {}).get("ohlc", {})
                            for candle in cumulative_volume_candles:
                                if( candle ["interval"]) == "1d":
                                    cumulative_volume = int(candle["vol"])
                                    break
                                elif (candle["interval"]) == "1I":
                                    cumulative_volume = int(candle["vol"])

                            if ltp is None:
                                continue

                            tick_data = {
                                "instrument_key": instrument_key,
                                "ltp": ltp,
                                "volume": cumulative_volume,
                                "timestamp": ltt
                            }

                            print(f"Parsed Tick: {tick_data}")

                            # Send parsed tick to strategy handler
                            if message_handler:
                                message_handler(tick_data)

                        except Exception as tick_error:
                            print(f"Error parsing tick for {instrument_key}: {tick_error}")

                else:
                    print("Unknown message format received:", decoded_json)

            except json.JSONDecodeError:
                print("JSON Decode Error: Message not valid JSON")
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                break


## Run standalone for quick test
"""
def call_back(message):
    print("from websocket client callback: ", message)

# Execute the function to fetch market data
instrument_keys_input =['NSE_EQ|INE742F01042', 'NSE_EQ|INE758T01015', 'NSE_EQ|INE296A01032']
mode  = "full"

asyncio.run(fetch_market_data(instrument_keys_input, mode, call_back, access_token =  "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGNjZTk0ODI1Yjg1MjRmN2RkOGJmZDEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1ODI1OTUyOCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU4MzE5MjAwfQ.-vQFrG60jEPtedFCXL9tq3j31kf-9WruJZ1bzGr0inU"))
"""