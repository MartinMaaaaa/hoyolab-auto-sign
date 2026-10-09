"""Unit tests for game specifications and registry."""
from __future__ import annotations

import unittest

from hoyolab_checkin.games import GAME_REGISTRY, GameSpec


class TestGames(unittest.TestCase):
    """Test GAME_REGISTRY configuration."""

    def test_registry_contains_required_games(self) -> None:
        self.assertIn("genshin", GAME_REGISTRY)
        self.assertIn("star_rail", GAME_REGISTRY)
        self.assertIn("zzz", GAME_REGISTRY)

    def test_game_spec_attributes(self) -> None:
        genshin = GAME_REGISTRY["genshin"]
        self.assertEqual(genshin.act_id, "e202102251931481")
        self.assertTrue(genshin.sign_url.startswith("https://sg-hk4e-api.hoyolab.com"))

        star_rail = GAME_REGISTRY["star_rail"]
        self.assertEqual(star_rail.act_id, "e202303301540311")
        self.assertTrue(star_rail.sign_url.startswith("https://sg-public-api.hoyolab.com"))

        zzz = GAME_REGISTRY["zzz"]
        self.assertEqual(zzz.act_id, "e202406031448091")
        self.assertEqual(zzz.extra_headers.get("x-rpc-signgame"), "zzz")

    def test_game_spec_immutability(self) -> None:
        genshin = GAME_REGISTRY["genshin"]
        with self.assertRaises(Exception):
            genshin.key = "other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
