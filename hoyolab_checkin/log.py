"""Logging configuration and secret masking utilities."""
from __future__ import annotations

import logging
import sys


class _StdErrFilter(logging.Filter):
    """Filter to allow only WARNING and higher levels to stderr."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.WARNING


class _StdOutFilter(logging.Filter):
    """Filter to allow only INFO and DEBUG levels to stdout."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.WARNING


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger to route INFO to stdout and WARNING+ to stderr."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stdout handler for DEBUG and INFO
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.addFilter(_StdOutFilter())
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    # Stderr handler for WARNING, ERROR, CRITICAL
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(_StdErrFilter())
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)


def mask_secret(val: str | None) -> str:
    """Mask sensitive string, keeping first 6 and last 2 characters.

    If length is less than 10, returns '***'.
    """
    if not val:
        return ""
    val_str = str(val).strip()
    if len(val_str) < 10:
        return "***"
    return f"{val_str[:6]}…{val_str[-2:]}"
