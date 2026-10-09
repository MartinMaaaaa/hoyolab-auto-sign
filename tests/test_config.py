"""Unit tests for configuration loading."""
from __future__ import annotations

import unittest

from hoyolab_checkin.config import DEFAULT_APP_VERSION, DEFAULT_GAMES, load_config
from hoyolab_checkin.exceptions import ConfigError


class TestConfig(unittest.TestCase):
    """Test configuration parser and validator."""

    def test_missing_cookies_raises_error(self) -> None:
        with self.assertRaises(ConfigError):
            load_config({})

    def test_empty_cookies_raises_error(self) -> None:
        with self.assertRaises(ConfigError):
            load_config({"HOYOLAB_COOKIES": "   \n\n  "})

    def test_multi_account_cookies_parsing(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "cookie_one=123\n# this is a comment\ncookie_two=456\n\n",
        }
        config = load_config(env)
        self.assertEqual(len(config.cookies), 2)
        self.assertEqual(config.cookies[0], "cookie_one=123")
        self.assertEqual(config.cookies[1], "cookie_two=456")
        self.assertEqual(config.games, DEFAULT_GAMES)
        self.assertEqual(config.push_level, "fail_only")
        self.assertEqual(config.max_attempts, 3)
        self.assertEqual(config.retry_delay_seconds, 60.0)
        self.assertEqual(config.app_version, DEFAULT_APP_VERSION)

    def test_custom_games_parsing(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "HOYOLAB_GAMES": "genshin, zzz",
        }
        config = load_config(env)
        self.assertEqual(config.games, ("genshin", "zzz"))

    def test_unknown_game_raises_error(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "HOYOLAB_GAMES": "genshin, invalid_game",
        }
        with self.assertRaises(ConfigError) as ctx:
            load_config(env)
        self.assertIn("Unknown game key", str(ctx.exception))

    def test_invalid_push_level_raises_error(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "PUSH_LEVEL": "invalid_mode",
        }
        with self.assertRaises(ConfigError):
            load_config(env)

    def test_invalid_retry_attempts_raises_error(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "CHECKIN_MAX_ATTEMPTS": "-1",
        }
        with self.assertRaises(ConfigError):
            load_config(env)

    def test_invalid_retry_delay_raises_error(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "CHECKIN_RETRY_DELAY_SECONDS": "not_a_number",
        }
        with self.assertRaises(ConfigError):
            load_config(env)

    def test_all_custom_options(self) -> None:
        env = {
            "HOYOLAB_COOKIES": "c1=1",
            "PUSHPLUS_TOKEN": "token_pp",
            "TELEGRAM_BOT_TOKEN": "token_tg",
            "TELEGRAM_CHAT_ID": "chat_123",
            "PUSH_LEVEL": "all",
            "CHECKIN_MAX_ATTEMPTS": "5",
            "CHECKIN_RETRY_DELAY_SECONDS": "15.5",
            "HOYOLAB_APP_VERSION": "3.0.0",
            "HOYOLAB_USER_AGENT": "CustomUA/1.0",
        }
        config = load_config(env)
        self.assertEqual(config.pushplus_token, "token_pp")
        self.assertEqual(config.telegram_bot_token, "token_tg")
        self.assertEqual(config.telegram_chat_id, "chat_123")
        self.assertEqual(config.push_level, "all")
        self.assertEqual(config.max_attempts, 5)
        self.assertEqual(config.retry_delay_seconds, 15.5)
        self.assertEqual(config.app_version, "3.0.0")
        self.assertEqual(config.user_agent, "CustomUA/1.0")


if __name__ == "__main__":
    unittest.main()
