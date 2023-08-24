"""Contains the function to setup the logger.

Functions:
    setup_logger()
"""

from __future__ import annotations

from logging import DEBUG as LOG_DEBUG
from logging import (
    ERROR,
    INFO,
    WARNING,
    Formatter,
    LogRecord,
    StreamHandler,
    basicConfig,
)
from typing import ClassVar

from src.consts import DEBUG


class _CustomFormatter(Formatter):
    """Custom logging formater that colors logs based on log level."""

    default_format = "%(levelname)s %(message)s"

    colors: ClassVar[dict[str, int]] = {
        LOG_DEBUG: 37, # White
        INFO:      34, # Blue
        WARNING:   33, # Yellow
        ERROR:     31, # Red
    }

    def format(self, record: LogRecord) -> str:  # noqa: A003

        color = self.colors.get(record.levelno, 0)
        self._style._fmt = ( # pylint: disable=protected-access  # noqa: SLF001
            f"\033[{color}m" + \
            self.default_format + \
            "\033[0m"
        )

        return super().format(record)

def setup_logger() -> None:
    """Setup the logger."""
    console_handler = StreamHandler()
    console_handler.setFormatter(_CustomFormatter())

    basicConfig(
        level=LOG_DEBUG if DEBUG else INFO,
        handlers=[
            console_handler,
        ],
    )
