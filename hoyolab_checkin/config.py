"""Environment configuration loader and validator."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .exceptions import ConfigError
from .games import GAME_REGISTRY

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)
DEFAULT_APP_VERSION = "2.34.1"
DEFAULT_GAMES = ("genshin", "star_rail", "zzz")


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable application configuration."""

    cookies: tuple[str, ...]
    games: tuple[str, ...]
    pushplus_token: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    push_level: str = "fail_only"
    max_attempts: int = 3
    retry_delay_seconds: float = 60.0
    app_version: str = DEFAULT_APP_VERSION
    user_agent: str = DEFAULT_USER_AGENT


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """Load and validate configuration strictly from environment variables.

    Raises:
        ConfigError: If required variables are missing or values are invalid.
    """
    if env is None:
        env = os.environ

    # Parse cookies (required)
    raw_cookies = env.get("HOYOLAB_COOKIES", "")
    if not raw_cookies or not raw_cookies.strip():
        raise ConfigError("Missing or empty HOYOLAB_COOKIES environment variable")

    parsed_cookies = tuple(
        line.strip()
        for line in raw_cookies.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if not parsed_cookies:
        raise ConfigError("No valid cookie strings found in HOYOLAB_COOKIES")

    # Parse games (optional)
    raw_games = env.get("HOYOLAB_GAMES", "")
    if raw_games and raw_games.strip():
        games_list = [g.strip() for g in raw_games.split(",") if g.strip()]
        for game_key in games_list:
            if game_key not in GAME_REGISTRY:
                raise ConfigError(
                    f"Unknown game key '{game_key}' in HOYOLAB_GAMES. "
                    f"Supported games: {list(GAME_REGISTRY.keys())}"
                )
        parsed_games = tuple(games_list)
        if not parsed_games:
            raise ConfigError("HOYOLAB_GAMES cannot be empty when specified")
    else:
        parsed_games = DEFAULT_GAMES

    # Notifications
    pushplus_token = env.get("PUSHPLUS_TOKEN", "").strip() or None
    telegram_bot_token = env.get("TELEGRAM_BOT_TOKEN", "").strip() or None
    telegram_chat_id = env.get("TELEGRAM_CHAT_ID", "").strip() or None

    # Push level
    push_level = env.get("PUSH_LEVEL", "fail_only").strip()
    if push_level not in ("fail_only", "all"):
        raise ConfigError(
            f"Invalid PUSH_LEVEL '{push_level}'. Allowed values: 'fail_only', 'all'"
        )

    # Retry settings
    raw_max_attempts = env.get("CHECKIN_MAX_ATTEMPTS", "3").strip()
    try:
        max_attempts = int(raw_max_attempts)
        if max_attempts <= 0:
            raise ValueError()
    except ValueError:
        raise ConfigError(
            f"CHECKIN_MAX_ATTEMPTS must be a positive integer, got '{raw_max_attempts}'"
        )

    raw_delay = env.get("CHECKIN_RETRY_DELAY_SECONDS", "60").strip()
    try:
        retry_delay_seconds = float(raw_delay)
        if retry_delay_seconds < 0:
            raise ValueError()
    except ValueError:
        raise ConfigError(
            f"CHECKIN_RETRY_DELAY_SECONDS must be a non-negative number, got '{raw_delay}'"
        )

    # Headers
    app_version = env.get("HOYOLAB_APP_VERSION", "").strip() or DEFAULT_APP_VERSION
    user_agent = env.get("HOYOLAB_USER_AGENT", "").strip() or DEFAULT_USER_AGENT

    return Config(
        cookies=parsed_cookies,
        games=parsed_games,
        pushplus_token=pushplus_token,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        push_level=push_level,
        max_attempts=max_attempts,
        retry_delay_seconds=retry_delay_seconds,
        app_version=app_version,
        user_agent=user_agent,
    )
