"""Game registry and specification definitions."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GameSpec:
    """Immutable game specification and API endpoint definitions."""

    key: str
    name: str
    act_id: str
    sign_url: str
    info_url: str
    extra_headers: dict[str, str] = field(default_factory=dict)


# Supported games registry
GAME_REGISTRY: dict[str, GameSpec] = {
    "genshin": GameSpec(
        key="genshin",
        name="原神",
        act_id="e202102251931481",
        sign_url=(
            "https://sg-hk4e-api.hoyolab.com/event/sol/sign"
            "?lang=en-us&act_id=e202102251931481"
        ),
        info_url=(
            "https://sg-hk4e-api.hoyolab.com/event/sol/info"
            "?lang=en-us&act_id=e202102251931481"
        ),
    ),
    "star_rail": GameSpec(
        key="star_rail",
        name="崩坏：星穹铁道",
        act_id="e202303301540311",
        sign_url=(
            "https://sg-public-api.hoyolab.com/event/luna/os/sign"
            "?lang=en-us&act_id=e202303301540311"
        ),
        info_url=(
            "https://sg-public-api.hoyolab.com/event/luna/os/info"
            "?lang=en-us&act_id=e202303301540311"
        ),
    ),
    "zzz": GameSpec(
        key="zzz",
        name="绝区零",
        act_id="e202406031448091",
        sign_url=(
            "https://sg-public-api.hoyolab.com/event/luna/zzz/os/sign"
            "?lang=en-us&act_id=e202406031448091"
        ),
        info_url=(
            "https://sg-public-api.hoyolab.com/event/luna/zzz/os/info"
            "?lang=en-us&act_id=e202406031448091"
        ),
        extra_headers={"x-rpc-signgame": "zzz"},
    ),
    # Reserved games for future extension (v1 excluded):
    # honkai3 act_id: e202110291205111, sign: .../event/mani/sign
    # tears_of_themis act_id: e202308141137581, sign: .../event/luna/os/sign
}
