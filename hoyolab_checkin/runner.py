"""Check-in execution orchestrator across multiple accounts and games."""
from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass
from typing import Callable

from .api import CheckinStatus, HoyoLabClient
from .config import Config
from .games import GAME_REGISTRY
from .log import mask_secret

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GameResult:
    """Execution result for a single game check-in."""

    game_key: str
    game_name: str
    status: CheckinStatus
    message: str
    total_sign_day: int | None = None


@dataclass(frozen=True, slots=True)
class AccountResult:
    """Execution results for a single user account."""

    account_index: int
    account_id_masked: str
    game_results: tuple[GameResult, ...]


def _extract_account_identifier(cookie: str, index: int) -> str:
    """Extract and mask account identifier from cookie, fallback to masked index."""
    match = re.search(r"ltuid(?:_v2)?=(\d+)", cookie)
    if match:
        uid = match.group(1)
        return f"ltuid {mask_secret(uid)}"
    return f"账号 {index + 1} ({mask_secret(cookie)})"


def run_all(
    config: Config,
    client: HoyoLabClient | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[AccountResult]:
    """Execute check-in for all configured accounts and games with retry and random delays."""
    if client is None:
        client = HoyoLabClient(config)

    account_results: list[AccountResult] = []
    total_accounts = len(config.cookies)

    for acc_idx, cookie in enumerate(config.cookies):
        acc_label = _extract_account_identifier(cookie, acc_idx)
        logger.info(
            "Starting check-in for account [%s] (%d/%d)",
            acc_label,
            acc_idx + 1,
            total_accounts,
        )

        game_results_list: list[GameResult] = []

        for game_idx, game_key in enumerate(config.games):
            game_spec = GAME_REGISTRY[game_key]
            logger.info("[%s] Checking sign-in status for %s...", acc_label, game_spec.name)

            # Step 1: Query info endpoint (pre-check)
            info_status, info_data, info_msg = client.get_info(cookie, game_spec)

            total_days: int | None = None
            if isinstance(info_data, dict):
                total_days = info_data.get("total_sign_day")

            # If already signed today according to info pre-check
            is_signed_today = (
                info_status == CheckinStatus.SUCCESS
                and isinstance(info_data, dict)
                and info_data.get("is_sign")
            )
            if is_signed_today:
                logger.info(
                    "[%s] %s already signed today (day %s). Skipping sign.",
                    acc_label,
                    game_spec.name,
                    total_days,
                )
                game_results_list.append(
                    GameResult(
                        game_key=game_spec.key,
                        game_name=game_spec.name,
                        status=CheckinStatus.ALREADY_SIGNED,
                        message="今日已签",
                        total_sign_day=total_days,
                    )
                )
            else:
                # Anti-risk jitter sleep before sign request
                sleeper(random.uniform(3.0, 8.0))

                # Step 2: Retry loop for sign endpoint
                attempt = 0
                final_status = CheckinStatus.NET_ERR
                final_msg = info_msg

                while attempt < config.max_attempts:
                    attempt += 1
                    logger.info(
                        "[%s] Attempt %d/%d signing %s...",
                        acc_label,
                        attempt,
                        config.max_attempts,
                        game_spec.name,
                    )
                    final_status, sign_data, final_msg = client.sign(cookie, game_spec)

                    # Non-retryable conditions
                    if final_status in (
                        CheckinStatus.SUCCESS,
                        CheckinStatus.ALREADY_SIGNED,
                        CheckinStatus.CAPTCHA_RISK,
                        CheckinStatus.INVALID_COOKIE,
                    ):
                        break

                    # Retryable error encountered
                    if attempt < config.max_attempts:
                        logger.warning(
                            "[%s] Sign %s encountered retryable status %s (%s). Retrying in %ss...",
                            acc_label,
                            game_spec.name,
                            final_status.value,
                            mask_secret(final_msg),
                            config.retry_delay_seconds,
                        )
                        sleeper(config.retry_delay_seconds)

                # Calculate updated total_days on success
                if final_status == CheckinStatus.SUCCESS and total_days is not None:
                    total_days += 1

                game_results_list.append(
                    GameResult(
                        game_key=game_spec.key,
                        game_name=game_spec.name,
                        status=final_status,
                        message=final_msg,
                        total_sign_day=total_days,
                    )
                )

            # Random interval between games (3-8 seconds)
            if game_idx < len(config.games) - 1:
                sleeper(random.uniform(3.0, 8.0))

        account_results.append(
            AccountResult(
                account_index=acc_idx + 1,
                account_id_masked=acc_label,
                game_results=tuple(game_results_list),
            )
        )

        # Random interval between accounts (5-15 seconds)
        if acc_idx < total_accounts - 1:
            sleeper(random.uniform(5.0, 15.0))

    return account_results
