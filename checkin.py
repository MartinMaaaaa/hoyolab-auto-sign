"""Main entry point for HoYoLAB automatic check-in."""
from __future__ import annotations

import logging
import sys

from hoyolab_checkin.api import CheckinStatus
from hoyolab_checkin.config import load_config
from hoyolab_checkin.exceptions import ConfigError
from hoyolab_checkin.log import setup_logging
from hoyolab_checkin.news import fetch_daily_news
from hoyolab_checkin.notify import send_report
from hoyolab_checkin.runner import run_all

logger = logging.getLogger("checkin")


def main() -> int:
    """Run check-in pipeline and return process exit code."""
    setup_logging()

    try:
        config = load_config()
    except ConfigError as err:
        logger.error("Configuration error: %s", str(err))
        return 1

    logger.info(
        "Configuration loaded: %d account(s), %d game(s)",
        len(config.cookies),
        len(config.games),
    )
    results = run_all(config)

    # Fetch daily Canada news update if enabled
    news_item = None
    if config.enable_news:
        try:
            logger.info("Fetching daily Canada news update...")
            news_item = fetch_daily_news(config)
            if news_item:
                logger.info(
                    "Daily news selected: '%s' (%s)", news_item.title, news_item.source
                )
            else:
                logger.info("No matching news found within 2 days meeting all criteria.")
        except Exception as err:
            logger.warning("Failed to fetch daily news update: %s", str(err))

    # Deliver notifications
    send_report(results, config, news_item=news_item)

    # Determine exit code: 0 if all succeeded or already signed; 1 if any failed
    all_successful = all(
        gr.status in (CheckinStatus.SUCCESS, CheckinStatus.ALREADY_SIGNED)
        for ar in results
        for gr in ar.game_results
    )

    if all_successful:
        logger.info("All check-in tasks completed successfully.")
        return 0

    logger.warning("One or more check-in tasks failed or encountered risk verification.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
