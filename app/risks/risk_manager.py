
class RiskManager:
    def __init__(self, max_positions=3, stop_loss_pct=0.02, take_profit_pct=0.04, max_daily_loss=10000):
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss

        self.current_loss = 0
        self.open_positions = {}  # {symbol: {"entry_price": float, "qty": int}}

    def can_open_new_position(self):
        """Check if a new position can be opened."""
        if len(self.open_positions) >= self.max_positions:
            return False, "Max positions limit reached"
        return True, ""

    def record_trade(self, symbol, qty, price, side):
        """Update open positions and track realized PnL."""
        if side == "BUY":
            self.open_positions[symbol] = {"entry_price": price, "qty": qty}
        elif side == "SELL" and symbol in self.open_positions:
            position = self.open_positions.pop(symbol)
            pnl = (price - position["entry_price"]) * position["qty"]
            self.current_loss += pnl

    def check_stop_loss_take_profit(self, symbol, current_price):
        """Check if stop-loss or take-profit is triggered for a given position."""
        if symbol not in self.open_positions:
            return None, None

        position = self.open_positions[symbol]
        entry_price = position["entry_price"]

        stop_loss_price = entry_price * (1 - self.stop_loss_pct)
        take_profit_price = entry_price * (1 + self.take_profit_pct)

        if current_price <= stop_loss_price:
            return "SELL", "Stop loss triggered"
        elif current_price >= take_profit_price:
            return "SELL", "Take profit triggered"

        return None, None

    def check_daily_loss_limit(self):
        """Check if total losses exceed the daily threshold."""
        if self.current_loss <= -self.max_daily_loss:
            return False, "Daily loss limit exceeded"
        return True, ""
