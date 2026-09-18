"""Centralized logging configuration for ClearClause monitoring."""

import logging
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with unified format across application."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if already added
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers[0] = handler


def get_logger(name: str) -> logging.Logger:
    """Get named logger instance."""
    setup_logging()
    return logging.getLogger(name)
