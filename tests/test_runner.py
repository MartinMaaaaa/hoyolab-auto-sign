"""Unit tests for checkin execution runner."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from hoyolab_checkin.api import CheckinStatus
from hoyolab_checkin.config import Config
from hoyolab_checkin.runner import run_all


class TestRunner(unittest.TestCase):
    """Test runner orchestration, pre-check, and retry behavior."""

    def setUp(self) -> None:
        self.mock_sleeper = MagicMock()

    def test_info_already_signed_skips_sign(self) -> None:
        config = Config(cookies=("ltuid_v2=123456789; ltoken_v2=abc;",), games=("genshin",))
        mock_client = MagicMock()
        # info returns already signed
        mock_client.get_info.return_value = (
            CheckinStatus.SUCCESS,
            {"is_sign": True, "total_sign_day": 8},
            "OK",
        )

        results = run_all(config, client=mock_client, sleeper=self.mock_sleeper)

        self.assertEqual(len(results), 1)
        game_res = results[0].game_results[0]
        self.assertEqual(game_res.status, CheckinStatus.ALREADY_SIGNED)
        self.assertEqual(game_res.total_sign_day, 8)
        # Verify sign was NEVER called
        mock_client.sign.assert_not_called()

    def test_sign_success_updates_day_count(self) -> None:
        config = Config(cookies=("ltuid=1234567890; ltoken=abc;",), games=("genshin",))
        mock_client = MagicMock()
        # info returns not signed, day 5
        mock_client.get_info.return_value = (
            CheckinStatus.SUCCESS,
            {"is_sign": False, "total_sign_day": 5},
            "OK",
        )
        mock_client.sign.return_value = (CheckinStatus.SUCCESS, {}, "OK")

        results = run_all(config, client=mock_client, sleeper=self.mock_sleeper)

        game_res = results[0].game_results[0]
        self.assertEqual(game_res.status, CheckinStatus.SUCCESS)
        self.assertEqual(game_res.total_sign_day, 6)
        mock_client.sign.assert_called_once()

    def test_captcha_risk_does_not_retry(self) -> None:
        config = Config(cookies=("cookie_1",), games=("star_rail",), max_attempts=3)
        mock_client = MagicMock()
        mock_client.get_info.return_value = (CheckinStatus.SUCCESS, {"is_sign": False}, "OK")
        mock_client.sign.return_value = (CheckinStatus.CAPTCHA_RISK, {}, "Risk triggered")

        results = run_all(config, client=mock_client, sleeper=self.mock_sleeper)

        game_res = results[0].game_results[0]
        self.assertEqual(game_res.status, CheckinStatus.CAPTCHA_RISK)
        # Must only call sign once (no retry!)
        self.assertEqual(mock_client.sign.call_count, 1)

    def test_invalid_cookie_does_not_retry(self) -> None:
        config = Config(cookies=("cookie_1",), games=("zzz",), max_attempts=3)
        mock_client = MagicMock()
        mock_client.get_info.return_value = (CheckinStatus.SUCCESS, {"is_sign": False}, "OK")
        mock_client.sign.return_value = (CheckinStatus.INVALID_COOKIE, {}, "Please log in")

        results = run_all(config, client=mock_client, sleeper=self.mock_sleeper)

        game_res = results[0].game_results[0]
        self.assertEqual(game_res.status, CheckinStatus.INVALID_COOKIE)
        # Must only call sign once (no retry!)
        self.assertEqual(mock_client.sign.call_count, 1)

    def test_net_err_retries_up_to_max_attempts(self) -> None:
        config = Config(cookies=("cookie_1",), games=("genshin",), max_attempts=3)
        mock_client = MagicMock()
        mock_client.get_info.return_value = (CheckinStatus.SUCCESS, {"is_sign": False}, "OK")
        mock_client.sign.return_value = (CheckinStatus.NET_ERR, {}, "Connection error")

        results = run_all(config, client=mock_client, sleeper=self.mock_sleeper)

        game_res = results[0].game_results[0]
        self.assertEqual(game_res.status, CheckinStatus.NET_ERR)
        # Must attempt 3 times
        self.assertEqual(mock_client.sign.call_count, 3)


if __name__ == "__main__":
    unittest.main()
