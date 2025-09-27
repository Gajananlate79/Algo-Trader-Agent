import requests

# Your authentication token
access_token = 'eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGI4MmY1ZTAwZDczMDZmZDY5YmNiMTQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU2OTAxMjE0LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk0NDI0MDB9.l3-8fK1yq6RSSk2yqcYMn-qIJydQJTVs1H-L8knjy7M'

# Path parameters
instrument_key = 'NSE_EQ|INE009A01021'
unit = 'minutes'
interval = '5'
to_date = '2025-09-03'
from_date = '2025-09-03' # Optional

#This is live API so need token for live api.
url = 'https://api.upstox.com/v3/market-quote/ohlc'

# Headers for the API request
headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0U0FFQlUiLCJqdGkiOiI2OGJhZGYzMjU1MTQ0OTZlMzMxMTVhMzkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc1NzA3NzI5OCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzU3MTA5NjAwfQ.n7ADnPVDhLfq1dglWuZqGkdCBiJ-9XiqYNnqIZVcg6g',
}

data = {
    "instrument_key": "NSE_EQ|INE002A01018,NSE_EQ|INE009A01021",
    "interval": "I5"
}


response = requests.get(url, headers=headers, params=data)

print(response.status_code)
print(response.json())


