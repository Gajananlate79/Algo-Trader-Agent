df = broker.get_intraday_ohlc(
    instrument_keys=["NSE_EQ|INE467B01029"],
    interval="I5",
    from_date="2025-06-01",
    to_date="2025-09-05"
)
print(df.head())
