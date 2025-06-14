import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from app.config import Config


class Logger:
    _instance = None

    def __new__(cls, log_dir="logs/scope_tree_violations"):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._init_logger(log_dir, Config.DEBUG)
        return cls._instance

    def _init_logger(self, log_dir, debug):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_filename = os.path.join(log_dir, datetime.now().strftime("%Y-%m-%d.log"))
        self.logger = logging.getLogger("CustomLogger")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = TimedRotatingFileHandler(
            log_filename, when="midnight", interval=1, backupCount=7
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"
        self.logger.addHandler(file_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


# Create a global logger instance
logger = Logger()
