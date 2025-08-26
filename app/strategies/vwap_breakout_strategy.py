import backtrader as bt
from datetime import time

# -----------------------------
# Custom VWAP Indicator
# -----------------------------
class VWAP(bt.Indicator):
    lines = ('vwap',)
    params = (('period', 1),)

    def __init__(self):
        self.addminperiod(1)
        self.cum_vp = 0.0
        self.cum_vol = 0.0

    def next(self):
        price = self.data.close[0]
        vol = self.data.volume[0]
        self.cum_vp += price * vol
        self.cum_vol += vol
        self.lines.vwap[0] = self.cum_vp / self.cum_vol if self.cum_vol != 0 else 0.0


# -----------------------------
# VWAP Breakout Strategy
# -----------------------------
class VWAPBreakoutStrategy(bt.Strategy):
    params = dict(
        broker=None,
        trade_logger=None,
        risk_manager=None,
        stop_loss_pct=0.005,
        volume_period=20,
        start_time=time(9,45),
        allow_short=True
    )

    def __init__(self):
        self.vwap = VWAP(self.data)
        self.mock_positions = {}

    def next(self):
        if self.data.datetime.time() < self.p.start_time:
            return

        symbol = self.data._name
        price = self.data.close[0]
        qty = 1

        if symbol in self.mock_positions:
            self._check_stop_loss(symbol, price)
            return

        if self.p.risk_manager and not self.p.risk_manager.can_trade(symbol, price, qty):
            return

        avg_vol = sum(self.data.volume.get(size=self.p.volume_period)) / self.p.volume_period
        if self.data.volume[0] < avg_vol:
            return

        # LONG breakout
        if price > self.vwap[0] and self.data.close[-1] <= self.vwap[-1]:
            self._open_mock_position(symbol, price, qty, is_buy=True)
        # SHORT breakout
        elif self.p.allow_short and price < self.vwap[0] and self.data.close[-1] >= self.vwap[-1]:
            self._open_mock_position(symbol, price, qty, is_buy=False)

    def _open_mock_position(self, symbol, price, qty, is_buy=True):
        side = "BUY" if is_buy else "SELL"
        stop_price = price * (1 - self.p.stop_loss_pct) if is_buy else price * (1 + self.p.stop_loss_pct)
        self.mock_positions[symbol] = {"price": price, "qty": qty, "side": side, "stop_price": stop_price}

        if self.p.risk_manager:
            self.p.risk_manager.update(symbol, side, qty, price)

        if self.p.trade_logger:
            self.p.trade_logger.log("info", f"Paper Trade Executed | {side} {qty} {symbol} @ {price:.2f} | Stop: {stop_price:.2f}")

    def _check_stop_loss(self, symbol, current_price):
        pos = self.mock_positions[symbol]
        side = pos["side"]
        stop_price = pos["stop_price"]
        exit_trade = False

        if side == "BUY" and current_price <= stop_price:
            exit_trade = True
        elif side == "SELL" and current_price >= stop_price:
            exit_trade = True

        if exit_trade:
            qty = pos["qty"]
            entry_price = pos["price"]
            pnl = (current_price - entry_price) * qty if side == "BUY" else (entry_price - current_price) * qty

            if self.p.trade_logger:
                self.p.trade_logger.log("info", f"Paper Stop-Loss Hit | {side} {qty} {symbol} Exit @ {current_price:.2f} | P&L: {pnl:.2f}")

            del self.mock_positions[symbol]

            if self.p.risk_manager:
                self.p.risk_manager.daily_loss += max(0, -pnl)
