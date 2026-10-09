"""Unit tests for API client and response classification state machine."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import requests

from hoyolab_checkin.api import CheckinStatus, HoyoLabClient, classify_response
from hoyolab_checkin.config import Config
from hoyolab_checkin.games import GAME_REGISTRY


class TestApi(unittest.TestCase):
    """Test API client methods and response classification."""

    def test_classify_net_err_on_exception(self) -> None:
        err = requests.RequestException("Connection timeout")
        status = classify_response(200, None, exception=err)
        self.assertEqual(status, CheckinStatus.NET_ERR)

    def test_classify_success(self) -> None:
        data = {"retcode": 0, "message": "OK", "data": {"total_sign_day": 5}}
        status = classify_response(200, data)
        self.assertEqual(status, CheckinStatus.SUCCESS)

    def test_classify_captcha_risk(self) -> None:
        data = {
            "retcode": 0,
            "message": "OK",
            "data": {"gt_result": {"is_risk": True}},
        }
        status = classify_response(200, data)
        self.assertEqual(status, CheckinStatus.CAPTCHA_RISK)

        data_direct = {
            "retcode": 0,
            "message": "OK",
            "data": {"is_risk": True},
        }
        self.assertEqual(classify_response(200, data_direct), CheckinStatus.CAPTCHA_RISK)

    def test_classify_already_signed(self) -> None:
        data = {"retcode": -5003, "message": "Traveler, you have already signed in"}
        status = classify_response(200, data)
        self.assertEqual(status, CheckinStatus.ALREADY_SIGNED)

    def test_classify_invalid_cookie(self) -> None:
        data_login_msg = {"retcode": -100, "message": "Please log in"}
        self.assertEqual(classify_response(200, data_login_msg), CheckinStatus.INVALID_COOKIE)

        data_cookie_keyword = {"retcode": 9999, "message": "invalid cookie token"}
        self.assertEqual(classify_response(200, data_cookie_keyword), CheckinStatus.INVALID_COOKIE)

    def test_classify_api_err(self) -> None:
        # HTTP 500
        self.assertEqual(classify_response(500, None), CheckinStatus.API_ERR)
        # HTTP 429
        self.assertEqual(classify_response(429, {"retcode": 429}), CheckinStatus.API_ERR)
        # Unknown retcode
        data_other = {"retcode": -1234, "message": "internal system error"}
        self.assertEqual(classify_response(200, data_other), CheckinStatus.API_ERR)

    def test_client_get_info_mocked(self) -> None:
        config = Config(cookies=("cookie_sample",), games=("genshin",))
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "retcode": 0,
            "message": "OK",
            "data": {"is_sign": True, "total_sign_day": 10},
        }
        session.get.return_value = mock_resp

        client = HoyoLabClient(config=config, session=session)
        status, data, msg = client.get_info("cookie_sample", GAME_REGISTRY["genshin"])

        self.assertEqual(status, CheckinStatus.SUCCESS)
        self.assertIsNotNone(data)
        self.assertTrue(data.get("is_sign"))
        self.assertEqual(data.get("total_sign_day"), 10)
        session.get.assert_called_once()

    def test_client_sign_zzz_extra_header(self) -> None:
        config = Config(cookies=("cookie_sample",), games=("zzz",))
        session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0, "message": "OK", "data": {}}
        session.post.return_value = mock_resp

        client = HoyoLabClient(config=config, session=session)
        status, data, msg = client.sign("cookie_sample", GAME_REGISTRY["zzz"])

        self.assertEqual(status, CheckinStatus.SUCCESS)
        # Verify extra headers were sent
        called_args, called_kwargs = session.post.call_args
        sent_headers = called_kwargs.get("headers", {})
        self.assertEqual(sent_headers.get("x-rpc-signgame"), "zzz")
        self.assertEqual(sent_headers.get("Cookie"), "cookie_sample")


if __name__ == "__main__":
    unittest.main()
