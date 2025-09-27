import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, log_file="logs/trading.log", logger_name = "TradingBot", level=logging.INFO):
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger(logger_name) #user can set it if needed
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent log duplication

        if not self.logger.handlers:
            # File handler
            file_handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def log(self, level, message):
        if level.lower() == "info":
            self.logger.info(message)
        elif level.lower() == "warning":
            self.logger.warning(message)
        elif level.lower() == "error":
            self.logger.error(message)
        else:
            self.logger.debug(message)
