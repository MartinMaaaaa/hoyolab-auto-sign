"""Unit tests for notification formatting and dispatching."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from hoyolab_checkin.api import CheckinStatus
from hoyolab_checkin.config import Config
from hoyolab_checkin.notify import format_report, send_report
from hoyolab_checkin.runner import AccountResult, GameResult


class TestNotify(unittest.TestCase):
    """Test notification report generation and delivery."""

    def test_format_report_content(self) -> None:
        results = [
            AccountResult(
                account_index=1,
                account_id_masked="ltuid 123***89",
                game_results=(
                    GameResult("genshin", "原神", CheckinStatus.SUCCESS, "OK", 8),
                    GameResult("star_rail", "崩坏：星穹铁道", CheckinStatus.ALREADY_SIGNED, "今日已签", 8),
                    GameResult("zzz", "绝区零", CheckinStatus.CAPTCHA_RISK, "风控", None),
                ),
            )
        ]
        report = format_report(results, date_str="2026-10-09")
        self.assertIn("🎮 HoYoLAB 签到报告 2026-10-09 (UTC)", report)
        self.assertIn("账号 1（ltuid 123***89）", report)
        self.assertIn("✅ 原神：签到成功（本月第 8 天）", report)
        self.assertIn("⏭️ 崩坏：星穹铁道：今日已签（本月第 8 天）", report)
        self.assertIn("⚠️ 绝区零：触发风控验证码，需人工处理", report)
        self.assertIn("统计：成功 1 / 已签 1 / 失败 1 —— 共 3 项", report)

    @patch("hoyolab_checkin.notify.requests.post")
    def test_push_level_fail_only_skips_when_all_success(
        self, mock_post: unittest.mock.MagicMock
    ) -> None:
        config = Config(
            cookies=("c1",),
            games=("genshin",),
            pushplus_token="mock_pp_token",
            push_level="fail_only",
        )
        results = [
            AccountResult(
                account_index=1,
                account_id_masked="acc1",
                game_results=(
                    GameResult("genshin", "原神", CheckinStatus.SUCCESS, "OK", 1),
                ),
            )
        ]
        send_report(results, config)
        mock_post.assert_not_called()

    @patch("hoyolab_checkin.notify.requests.post")
    def test_push_level_fail_only_sends_when_failure_exists(
        self, mock_post: unittest.mock.MagicMock
    ) -> None:
        config = Config(
            cookies=("c1",),
            games=("genshin",),
            pushplus_token="mock_pp_token",
            push_level="fail_only",
        )
        results = [
            AccountResult(
                account_index=1,
                account_id_masked="acc1",
                game_results=(
                    GameResult("genshin", "原神", CheckinStatus.API_ERR, "error", None),
                ),
            )
        ]
        mock_post.return_value.status_code = 200
        send_report(results, config)
        mock_post.assert_called_once()

    @patch("hoyolab_checkin.notify.requests.post")
    def test_telegram_and_pushplus_dual_dispatch(self, mock_post: unittest.mock.MagicMock) -> None:
        config = Config(
            cookies=("c1",),
            games=("genshin",),
            pushplus_token="mock_pp_token",
            telegram_bot_token="mock_tg_token",
            telegram_chat_id="12345678",
            push_level="all",
        )
        results = [
            AccountResult(
                account_index=1,
                account_id_masked="acc1",
                game_results=(
                    GameResult("genshin", "原神", CheckinStatus.SUCCESS, "OK", 1),
                ),
            )
        ]
        mock_post.return_value.status_code = 200
        send_report(results, config)
        # Should call both Telegram and PushPlus
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
