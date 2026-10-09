"""Unit tests for log configuration and secret masking."""
from __future__ import annotations

import unittest

from hoyolab_checkin.log import mask_secret, setup_logging


class TestLog(unittest.TestCase):
    """Test log utilities and secret masking."""

    def test_mask_secret_empty(self) -> None:
        self.assertEqual(mask_secret(""), "")
        self.assertEqual(mask_secret(None), "")

    def test_mask_secret_short(self) -> None:
        self.assertEqual(mask_secret("12345"), "***")
        self.assertEqual(mask_secret("123456789"), "***")

    def test_mask_secret_standard(self) -> None:
        result = mask_secret("abcdef1234567890")
        self.assertEqual(result, "abcdef…90")

    def test_setup_logging_runs(self) -> None:
        # Verify setup_logging runs without exception
        setup_logging()


if __name__ == "__main__":
    unittest.main()
