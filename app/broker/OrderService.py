import requests
import json

url = "https://api-sandbox.upstox.com/v3/order/place"

payload = json.dumps({
  "quantity": 1,
  "product": "D",
  "validity": "DAY",
  "price": 0,
  "tag": "string",
  "instrument_token": "NSE_EQ|INE848E01016",
  "order_type": "MARKET",
  "transaction_type": "BUY",
  "disclosed_quantity": 0,
  "trigger_price": 0,
  "is_amo": False,
  "slice": True
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGI4MmY1ZTAwZDczMDZmZDY5YmNiMTQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU2OTAxMjE0LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk0NDI0MDB9.l3-8fK1yq6RSSk2yqcYMn-qIJydQJTVs1H-L8knjy7M'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)