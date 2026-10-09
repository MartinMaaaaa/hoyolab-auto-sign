"""Custom exception hierarchy for hoyolab_checkin."""
from __future__ import annotations


class CheckinError(Exception):
    """Base exception for all checkin operations."""


class ConfigError(CheckinError):
    """Raised when environment variables or configurations are missing or invalid."""


class ApiError(CheckinError):
    """Raised when HTTP communication or response parsing fails."""


class NotifyError(CheckinError):
    """Raised when notification delivery fails (non-fatal)."""
