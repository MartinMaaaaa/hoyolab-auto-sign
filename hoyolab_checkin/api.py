"""HoYoLAB API client and response classification state machine."""
from __future__ import annotations

import enum
import logging
from typing import Any

import requests

from .config import Config
from .games import GameSpec
from .log import mask_secret

logger = logging.getLogger(__name__)


class CheckinStatus(enum.StrEnum):
    """Categorized status for check-in attempts."""

    SUCCESS = "SUCCESS"
    ALREADY_SIGNED = "ALREADY_SIGNED"
    CAPTCHA_RISK = "CAPTCHA_RISK"
    INVALID_COOKIE = "INVALID_COOKIE"
    API_ERR = "API_ERR"
    NET_ERR = "NET_ERR"


def classify_response(
    status_code: int,
    data: dict[str, Any] | None = None,
    exception: Exception | None = None,
) -> CheckinStatus:
    """Classify API response according to the specification state machine.

    Branches:
    1. requests exception / timeout -> NET_ERR (retryable)
    2. retcode 0 & gt_result.is_risk True -> CAPTCHA_RISK (no retry)
    3. retcode 0 -> SUCCESS
    4. retcode -5003 -> ALREADY_SIGNED (no retry)
    5. login / cookie invalid message features -> INVALID_COOKIE (no retry)
    6. other non-zero retcodes / HTTP 5xx / 429 -> API_ERR (retryable)
    """
    if exception is not None:
        return CheckinStatus.NET_ERR

    if status_code != 200:
        return CheckinStatus.API_ERR

    if not isinstance(data, dict):
        return CheckinStatus.API_ERR

    retcode = data.get("retcode")
    message = str(data.get("message", "")).lower()
    inner_data = data.get("data")

    # Success & Risk detection
    if retcode == 0:
        if isinstance(inner_data, dict):
            gt_result = inner_data.get("gt_result")
            if isinstance(gt_result, dict) and gt_result.get("is_risk"):
                return CheckinStatus.CAPTCHA_RISK
            if inner_data.get("is_risk") is True:
                return CheckinStatus.CAPTCHA_RISK
        return CheckinStatus.SUCCESS

    # Already signed
    if retcode == -5003:
        return CheckinStatus.ALREADY_SIGNED

    # Cookie invalid / not logged in
    login_keywords = ("login", "not logged in", "cookie", "authkey", "please log in")
    if retcode in (-100, 10001, -1071, -1073) or any(k in message for k in login_keywords):
        return CheckinStatus.INVALID_COOKIE

    # Other API errors (5xx, 429 or unexpected non-zero retcode)
    return CheckinStatus.API_ERR


class HoyoLabClient:
    """HTTP client communicating with HoYoLAB endpoints."""

    def __init__(
        self,
        config: Config,
        session: requests.Session | None = None,
        timeout: tuple[float, float] = (10.0, 30.0),
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.timeout = timeout

    def _build_headers(self, cookie: str, game: GameSpec) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://act.hoyolab.com",
            "Referer": "https://act.hoyolab.com/",
            "User-Agent": self.config.user_agent,
            "x-rpc-app_version": self.config.app_version,
            "x-rpc-client_type": "4",
            "Cookie": cookie,
        }
        if game.extra_headers:
            headers.update(game.extra_headers)
        return headers

    def get_info(
        self, cookie: str, game: GameSpec
    ) -> tuple[CheckinStatus, dict[str, Any] | None, str]:
        """Query sign-in status (pre-check)."""
        headers = self._build_headers(cookie, game)
        try:
            resp = self.session.get(game.info_url, headers=headers, timeout=self.timeout)
            status_code = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = None
            status = classify_response(status_code, data)
            msg = data.get("message", "") if isinstance(data, dict) else f"HTTP {status_code}"
            logger.debug(
                "[%s] info retcode=%s status=%s message=%s",
                game.key,
                data.get("retcode") if isinstance(data, dict) else status_code,
                status.value,
                mask_secret(msg),
            )
            return status, (data.get("data") if isinstance(data, dict) else None), msg
        except requests.RequestException as e:
            logger.warning("[%s] Network exception during get_info: %s", game.key, str(e))
            return CheckinStatus.NET_ERR, None, str(e)

    def sign(
        self, cookie: str, game: GameSpec
    ) -> tuple[CheckinStatus, dict[str, Any] | None, str]:
        """Perform sign-in request (POST)."""
        headers = self._build_headers(cookie, game)
        payload = {"act_id": game.act_id, "lang": "en-us"}
        try:
            resp = self.session.post(
                game.sign_url, json=payload, headers=headers, timeout=self.timeout
            )
            status_code = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = None
            status = classify_response(status_code, data)
            msg = data.get("message", "") if isinstance(data, dict) else f"HTTP {status_code}"
            logger.info(
                "[%s] sign retcode=%s status=%s message=%s",
                game.key,
                data.get("retcode") if isinstance(data, dict) else status_code,
                status.value,
                mask_secret(msg),
            )
            return status, (data.get("data") if isinstance(data, dict) else None), msg
        except requests.RequestException as e:
            logger.warning("[%s] Network exception during sign: %s", game.key, str(e))
            return CheckinStatus.NET_ERR, None, str(e)
