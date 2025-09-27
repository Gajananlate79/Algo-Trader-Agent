
# Nifty50 VWAP Bot (Upstock v3)

Intraday VWAP breakout bot that:
- Loads Nifty50 tickers from **Excel**.
- Ranks by Avg Volume × ATR, then trades **top 3**.
- Uses historical 5m OHLC for indicator warm-up.
- Places entry/SL/TP and manages a trailing stop via Upstock wrapper.
- Toggle **MOCK_MODE** for paper trading.

## Quickstart
1. Put your Excel at `data/nifty50.xlsx` (column name like SYMBOL). A sample will be created if missing.
2. Set environment vars:
```
export UPSTOCK_API_KEY=your_key
export UPSTOCK_ACCESS_TOKEN=your_token
```
3. Install: `pip install -r requirements.txt`
4. Run: `python main.py`

## Important
- `broker/upstock3_wrapper.py` contains placeholders for real SDK calls. Replace `NotImplementedError` with actual Upstock v3 API methods in your environment.
- Keep `MOCK_MODE=True` until you fully test.
