class RiskManager:
    def __init__(self, max_capital, max_loss_per_day, max_loss_per_trade):
        self.max_capital = max_capital
        self.max_loss_per_day = max_loss_per_day
        self.max_loss_per_trade = max_loss_per_trade
        self.daily_loss = 0

    def can_trade(self, symbol, price, qty):
        if self.daily_loss >= self.max_loss_per_day:
            return False
        return True

    def update(self, symbol, side, qty, price):
        self.daily_loss += 0
