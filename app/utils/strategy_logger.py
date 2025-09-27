
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

class StrategyLogger:
    def __init__(self, name: str = "nifty50_vwap_bot", log_file: str = "logs/strategy.log"):
        Path("logs").mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s"))

        fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

        if not self.logger.handlers:
            self.logger.addHandler(ch)
            self.logger.addHandler(fh)

    def log(self, level: str, msg: str):
        level = level.lower()
        getattr(self.logger, level if level in ("info","warning","error","debug") else "info")(msg)
