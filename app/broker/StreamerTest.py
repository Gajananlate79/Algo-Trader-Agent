from datetime import time

import upstox_client

# Replace with your access token from Step 2
access_token = "YOUR_ACCESS_TOKEN"

# Configure access token for authorization
configuration = upstox_client.Configuration()
configuration.access_token = access_token

# Define callback functions to handle events
def on_open(ws):
    print("WebSocket connection opened.")
    # Subscribe to the instruments once connected
    # Example: subscribe to NIFTY 50 futures
    upstox_streamer.subscribe(
        ['NSE_FO|30999'], # instrumentKeys
        'full'            # subscription mode: 'full' or 'ltpc'
    )

def on_message(ws, message):
    # This will be triggered on every new market update
    print("Message received:", message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws):
    print("WebSocket connection closed.")

def on_data(data):
    # This is a specific callback for the MarketDataStreamerV3
    print("Data received:", data)

# Initialize the Market Data Streamer client
upstox_streamer = upstox_client.MarketDataStreamerV3(
    api_client=upstox_client.ApiClient(configuration),

)

# Connect to the market data stream
try:
    upstox_streamer.connect()
    
except Exception as e:
    print("Failed to connect:", e)
