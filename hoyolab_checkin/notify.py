"""Notification dispatching for Telegram and PushPlus."""
from __future__ import annotations

import datetime
import logging
from typing import Sequence

import requests

from .api import CheckinStatus
from .config import Config
from .log import mask_secret
from .runner import AccountResult

logger = logging.getLogger(__name__)


def _status_to_line(
    game_name: str, status: CheckinStatus, total_days: int | None, message: str
) -> str:
    day_str = f"（本月第 {total_days} 天）" if total_days is not None else ""
    match status:
        case CheckinStatus.SUCCESS:
            return f"  ✅ {game_name}：签到成功{day_str}"
        case CheckinStatus.ALREADY_SIGNED:
            return f"  ⏭️ {game_name}：今日已签{day_str}"
        case CheckinStatus.CAPTCHA_RISK:
            return f"  ⚠️ {game_name}：触发风控验证码，需人工处理"
        case CheckinStatus.INVALID_COOKIE:
            return f"  ❌ {game_name}：Cookie 失效或未登录"
        case CheckinStatus.NET_ERR:
            return f"  ❌ {game_name}：网络请求失败"
        case CheckinStatus.API_ERR:
            brief_msg = f" ({mask_secret(message)})" if message else ""
            return f"  ❌ {game_name}：接口错误{brief_msg}"


def format_report(results: Sequence[AccountResult], date_str: str | None = None) -> str:
    """Format structured check-in results into notification message."""
    if date_str is None:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    lines = [f"🎮 HoYoLAB 签到报告 {date_str} (UTC)"]
    success_count = 0
    already_count = 0
    fail_count = 0

    for ar in results:
        lines.append(f"账号 {ar.account_index}（{ar.account_id_masked}）")
        for gr in ar.game_results:
            lines.append(_status_to_line(gr.game_name, gr.status, gr.total_sign_day, gr.message))
            if gr.status == CheckinStatus.SUCCESS:
                success_count += 1
            elif gr.status == CheckinStatus.ALREADY_SIGNED:
                already_count += 1
            else:
                fail_count += 1

    total_count = success_count + already_count + fail_count
    lines.append(
        f"统计：成功 {success_count} / 已签 {already_count} / 失败 {fail_count} —— 共 {total_count} 项"
    )
    return "\n".join(lines)


def send_report(results: Sequence[AccountResult], config: Config) -> None:
    """Send report to configured notification channels according to push level."""
    has_failure = any(
        gr.status not in (CheckinStatus.SUCCESS, CheckinStatus.ALREADY_SIGNED)
        for ar in results
        for gr in ar.game_results
    )

    if config.push_level == "fail_only" and not has_failure:
        logger.info("Push level is fail_only and all check-ins succeeded. Skipping notification.")
        return

    report = format_report(results)

    # 1. Telegram Bot
    if config.telegram_bot_token and config.telegram_chat_id:
        tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
        masked_tg_token = mask_secret(config.telegram_bot_token)
        try:
            logger.info("Sending notification via Telegram (token: %s)...", masked_tg_token)
            resp = requests.post(
                tg_url,
                json={"chat_id": config.telegram_chat_id, "text": report},
                timeout=(10.0, 15.0),
            )
            if resp.status_code == 200:
                logger.info("Telegram notification sent successfully.")
            else:
                logger.warning(
                    "Telegram notification returned HTTP %s: %s",
                    resp.status_code,
                    mask_secret(resp.text),
                )
        except requests.RequestException as e:
            logger.warning("Failed to send Telegram notification: %s", str(e))

    # 2. PushPlus
    if config.pushplus_token:
        pp_url = "http://www.pushplus.plus/send"
        masked_pp_token = mask_secret(config.pushplus_token)
        try:
            logger.info("Sending notification via PushPlus (token: %s)...", masked_pp_token)
            resp = requests.post(
                pp_url,
                json={
                    "token": config.pushplus_token,
                    "title": "HoYoLAB 签到报告",
                    "content": report,
                    "template": "txt",
                },
                timeout=(10.0, 15.0),
            )
            if resp.status_code == 200:
                logger.info("PushPlus notification sent successfully.")
            else:
                logger.warning(
                    "PushPlus notification returned HTTP %s: %s",
                    resp.status_code,
                    mask_secret(resp.text),
                )
        except requests.RequestException as e:
            logger.warning("Failed to send PushPlus notification: %s", str(e))
