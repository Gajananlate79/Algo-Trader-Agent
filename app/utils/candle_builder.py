
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class Candle:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

class CandleBuilder:
    def __init__(self, timeframe_minutes: int = 5):
        self.tf = timeframe_minutes
        self.current: Dict[str, Candle] = {}

    def _bucket_start(self, ts: datetime) -> datetime:
        minute = (ts.minute // self.tf) * self.tf
        return ts.replace(second=0, microsecond=0, minute=minute)

    def update(self, symbol: str, ltp: float, volume: float, ts: datetime):
        bucket = self._bucket_start(ts)
        c = self.current.get(symbol)
        if c is None or c.start != bucket:
            prev = self.current.get(symbol)
            self.current[symbol] = Candle(start=bucket, open=ltp, high=ltp, low=ltp, close=ltp, volume=volume or 0.0)
            return prev
        c.high = max(c.high, ltp)
        c.low = min(c.low, ltp)
        c.close = ltp
        c.volume = (c.volume or 0.0) + (volume or 0.0)
        return None

    def flush(self, symbol: str) -> Optional[Candle]:
        return self.current.pop(symbol, None)
