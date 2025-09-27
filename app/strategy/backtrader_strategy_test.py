import backtrader as bt
import pandas as pd

class TestStrategy(bt.Strategy):
    def next(self):
        print("Next bar executed")

# Create Cerebro engine
cerebro = bt.Cerebro()

# Create sample OHLC data
data = pd.DataFrame({
    'datetime': pd.date_range('2024-01-01', periods=5, freq='D'),
    'open': [100, 101, 102, 103, 104],
    'high': [101, 102, 103, 104, 105],
    'low': [99, 100, 101, 102, 103],
    'close': [100.5, 101.5, 102.5, 103.5, 104.5],
    'volume': [1000, 1100, 1200, 1300, 1400]
})

# Convert to Backtrader data feed
bt_data = bt.feeds.PandasData(
    dataname=data,
    datetime='datetime',
    open='open',
    high='high',
    low='low',
    close='close',
    volume='volume',
    openinterest=-1
)

# Add data and strategy
cerebro.adddata(bt_data)
cerebro.addstrategy(TestStrategy)

# Run Backtrader engine
cerebro.run()
