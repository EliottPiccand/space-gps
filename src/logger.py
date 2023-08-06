"""
Module containing the function to setup the logger
"""

from logging import DEBUG as LOG_DEBUG
from logging import ERROR, INFO, WARNING, Formatter, StreamHandler, basicConfig, LogRecord

from src.consts import DEBUG


class CustomFormatter(Formatter):
    """
    Custom logging formater that colors logs based on log level
    """

    default_format = "%(levelname)s %(message)s"

    colors = {
        LOG_DEBUG: 37, # White
        INFO:      34, # Blue
        WARNING:   33, # Yellow
        ERROR:     31, # Red
    }

    def format(self, record: LogRecord) -> str:

        color = self.colors.get(record.levelno, 0)
        self._style._fmt = f"\033[{color}m" + self.default_format + "\033[0m" # pylint: disable=protected-access

        return super().format(record)

def setup_logger():
    """
    Setup the logger
    """

    console_handler = StreamHandler()
    console_handler.setFormatter(CustomFormatter())

    basicConfig(
        level=LOG_DEBUG if DEBUG else INFO,
        handlers=[
            console_handler,
        ]
    )
