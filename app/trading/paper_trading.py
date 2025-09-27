import csv
import os

from app.utils.logger import Logger


class PaperTrader:
    def __init__(self, paper_trades_log_file='paper_trades.csv'):
        self.positions = {}
        self.closed_trades = []
        self.paper_trades_log_file = paper_trades_log_file
        # Set up logger
        self.logger = Logger('PaperTrader')

        # Write CSV header if file does not exist
        if not os.path.exists(self.paper_trades_log_file):
            with open(self.paper_trades_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['symbol', 'side', 'entry', 'exit', 'qty', 'pnl', 'reason'])
                writer.writeheader()

    def open_position(self, symbol, side, entry, stop, target, qty):
        self.positions[symbol] = {'side': side, 'entry': entry, 'stop': stop, 'target': target, 'qty': qty}

    def on_tick(self, symbol, price):
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos['side'] == 'BUY':
                if price <= pos['stop']:
                    pnl = (pos['stop'] - pos['entry']) * pos['qty']
                    self.close_position(symbol, pos['stop'], pnl, 'STOP LOSS')
                elif price >= pos['target']:
                    pnl = (pos['target'] - pos['entry']) * pos['qty']
                    self.close_position(symbol, pos['target'], pnl, 'TARGET')
            elif pos['side'] == 'SELL':
                if price >= pos['stop']:
                    pnl = (pos['entry'] - pos['stop']) * pos['qty']
                    self.close_position(symbol, pos['stop'], pnl, 'STOP LOSS')
                elif price <= pos['target']:
                    pnl = (pos['entry'] - pos['target']) * pos['qty']
                    self.close_position(symbol, pos['target'], pnl, 'TARGET')

    def close_position(self, symbol, exit_price, pnl, reason):
        pos = self.positions.pop(symbol)
        trade = {
            'symbol': symbol,
            'side': pos['side'],
            'entry': pos['entry'],
            'exit': exit_price,
            'qty': pos['qty'],
            'pnl': pnl,
            'reason': reason
        }
        self.closed_trades.append(trade)
        self.log_trades_to_file([trade])
        self.logger.log("info", f"Closed trade: {trade}")
        total_pnl = self.get_total_pnl()
        self.logger.log("info", f"Total PnL from paper trading after closing the position: {total_pnl}")

    def log_trades_to_file(self, trades):
        with open(self.paper_trades_log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'side', 'entry', 'exit', 'qty', 'pnl', 'reason'])
            for trade in trades:
                writer.writerow(trade)

    def get_total_pnl(self):
        return sum(trade['pnl'] for trade in self.closed_trades)
