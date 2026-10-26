"""Unit tests for Canadian daily news fetcher and filter."""
from __future__ import annotations

import datetime
import unittest
from unittest.mock import MagicMock, patch

from hoyolab_checkin.news import (
    NewsItem,
    calculate_score,
    clean_text,
    fetch_daily_news,
    format_news_block,
    format_relative_time,
    get_display_source,
    is_authoritative_source,
    is_canada_related,
    is_commercial,
    parse_feed_date,
    parse_items_from_xml,
    select_best_news,
    translate_to_zh,
)


class TestNews(unittest.TestCase):
    """Test news fetching, filtering, scoring, and formatting."""

    def test_clean_text(self) -> None:
        self.assertEqual(clean_text("<p>Hello &amp; <b>World</b></p>"), "Hello & World")
        self.assertEqual(clean_text("   Too   many   spaces   "), "Too many spaces")

    def test_parse_feed_date_rfc2822(self) -> None:
        dt = parse_feed_date("Sun, 25 Oct 2026 15:40:46 GMT")
        self.assertIsNotNone(dt)
        assert dt is not None
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 10)
        self.assertEqual(dt.day, 25)
        self.assertEqual(dt.tzinfo, datetime.timezone.utc)

    def test_parse_feed_date_iso8601(self) -> None:
        dt = parse_feed_date("2026-10-25T14:30:00Z")
        self.assertIsNotNone(dt)
        assert dt is not None
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.hour, 14)

        dt_offset = parse_feed_date("2026-10-25T11:00:00-04:00")
        self.assertIsNotNone(dt_offset)
        assert dt_offset is not None
        self.assertEqual(dt_offset.hour, 15)  # 11:00 -04:00 == 15:00 UTC

    def test_parse_feed_date_invalid(self) -> None:
        self.assertIsNone(parse_feed_date(None))
        self.assertIsNone(parse_feed_date(""))
        self.assertIsNone(parse_feed_date("not-a-valid-date-string"))

    def test_is_authoritative_source(self) -> None:
        # Whitelisted sources
        self.assertTrue(is_authoritative_source("CBC News", "https://www.cbc.ca/news/123"))
        self.assertTrue(is_authoritative_source("The Globe and Mail", "https://www.theglobeandmail.com/123"))
        self.assertTrue(is_authoritative_source("IRCC", "https://www.canada.ca/en/news/123"))
        self.assertTrue(is_authoritative_source("Radio-Canada", "https://ici.radio-canada.ca/123"))
        self.assertTrue(is_authoritative_source("Global News", "https://globalnews.ca/news/123"))
        self.assertTrue(is_authoritative_source("CTV News", "https://www.ctvnews.ca/123"))
        self.assertTrue(is_authoritative_source("Toronto Star", "https://www.thestar.com/123"))

        # Non-authoritative / unofficial sources
        self.assertFalse(is_authoritative_source("TechCrunch", "https://techcrunch.com/123"))
        self.assertFalse(is_authoritative_source("Personal Blog", "https://myblog.wordpress.com/123"))
        self.assertFalse(is_authoritative_source("PR Newswire", "https://prnewswire.com/123"))

    def test_get_display_source(self) -> None:
        self.assertIn("加拿大广播公司", get_display_source("CBC News"))
        self.assertIn("移民", get_display_source("IRCC"))
        self.assertIn("环球邮报", get_display_source("The Globe and Mail"))

    def test_is_commercial_filter(self) -> None:
        # Commercial / product releases / earnings should be True (blocked)
        self.assertTrue(is_commercial("Apple launches new iPad Pro with M4 chip in Canada"))
        self.assertTrue(is_commercial("Shopify releases quarterly earnings, shares surge 12%"))
        self.assertTrue(is_commercial("Tesla unveils new electric SUV lineup in Vancouver"))
        self.assertTrue(is_commercial("某公司发布最新AI大模型并在多伦多设立研发中心"))
        self.assertTrue(is_commercial("公司公布最新季度财报，净利润增长50%"))
        self.assertTrue(is_commercial("Black Friday mega discounts and promos across Ontario retail"))

        # Non-commercial public / policy / social news should be False (allowed)
        self.assertFalse(is_commercial("Smith scores slim majority on immigration questions in Alberta"))
        self.assertFalse(is_commercial("Changes to Express Entry for high-wage occupations announced by IRCC"))
        self.assertFalse(is_commercial("Tighter immigration rules put nursing homes at risk of losing workers"))
        self.assertFalse(is_commercial("Indian students in Ontario protest post-graduation work permit caps"))
        self.assertFalse(is_commercial("Chinese Canadian community marks anniversary of historic legislation"))

    def test_is_canada_related(self) -> None:
        # Canada-related news
        self.assertTrue(is_canada_related("Ottawa announces new immigration targets for 2027", "CBC News"))
        self.assertTrue(is_canada_related("Vancouver council votes on new housing policies", "The Globe and Mail"))
        self.assertTrue(is_canada_related("Alberta premier Danielle Smith addresses constitutional queries", "Global News"))
        self.assertTrue(is_canada_related("US-Canada border sees decrease in irregular crossings into Quebec", "CBC"))

        # US domestic news (should be filtered out)
        self.assertFalse(is_canada_related("Trump holds massive rally in Florida ahead of midterms", "US Politics"))
        self.assertFalse(is_canada_related("White House press secretary defends Biden administration economic policies in Texas", "AP"))
        self.assertFalse(is_canada_related("Congress debates California environmental regulations on Capitol Hill", "Reuters"))

    def test_calculate_score(self) -> None:
        # Immigration news scores higher than general Canada news
        immig_score = calculate_score("Canada updates Express Entry and PR rules for international students", "IRCC")
        general_score = calculate_score("Snowstorm hits Calgary causing minor highway delays", "CBC News")
        self.assertGreater(immig_score, general_score)

        # Chinese / Indian diaspora keywords give bonus score
        diaspora_score = calculate_score("Chinese Canadian and Indian newcomers adapt to Ontario job market", "CBC")
        self.assertGreater(diaspora_score, general_score)

    def test_parse_items_from_xml(self) -> None:
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Express Entry rules change - CBC</title>
                    <link>https://www.cbc.ca/news/express-entry</link>
                    <pubDate>Sun, 25 Oct 2026 12:00:00 GMT</pubDate>
                    <description>&lt;p&gt;Ottawa announced new guidelines.&lt;/p&gt;</description>
                    <source>CBC</source>
                </item>
            </channel>
        </rss>"""
        items = parse_items_from_xml(rss_xml, "CBC News")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Express Entry rules change")  # trailing ' - CBC' stripped
        self.assertEqual(items[0]["link"], "https://www.cbc.ca/news/express-entry")
        self.assertEqual(items[0]["summary"], "Ottawa announced new guidelines.")

        atom_xml = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>IRCC Minister announces new francophone immigration measures</title>
                <link href="https://www.canada.ca/en/news/ircc-announcement.html" />
                <published>2026-10-25T10:00:00Z</published>
                <summary>Measures designed to support French-speaking newcomers.</summary>
                <author><name>IRCC</name></author>
            </entry>
        </feed>"""
        atom_items = parse_items_from_xml(atom_xml, "IRCC")
        self.assertEqual(len(atom_items), 1)
        self.assertEqual(atom_items[0]["title"], "IRCC Minister announces new francophone immigration measures")
        self.assertEqual(atom_items[0]["link"], "https://www.canada.ca/en/news/ircc-announcement.html")
        self.assertEqual(atom_items[0]["source"], "IRCC")

    def test_select_best_news_time_filter(self) -> None:
        now = datetime.datetime(2026, 10, 26, 12, 0, tzinfo=datetime.timezone.utc)
        items = [
            # 1. 3 days ago -> should be dropped (exceeds 2 days limit)
            {
                "title": "Old Canada immigration news",
                "link": "https://www.cbc.ca/news/old",
                "pub_date": "Thu, 22 Oct 2026 12:00:00 GMT",
                "summary": "Old immigration policy details in Canada.",
                "source": "CBC News",
            },
            # 2. 1 day ago -> within 2 days -> should be selected
            {
                "title": "Fresh Canada immigration update",
                "link": "https://www.cbc.ca/news/fresh",
                "pub_date": "Sun, 25 Oct 2026 12:00:00 GMT",
                "summary": "Fresh immigration policy details for newcomers in Canada.",
                "source": "CBC News",
            },
        ]
        result = select_best_news(items, now=now, max_age_days=2)
        self.assertIsNotNone(result)
        assert result is not None
        best_item, _, score = result
        self.assertEqual(best_item["title"], "Fresh Canada immigration update")
        self.assertGreater(score, 0)

    def test_select_best_news_commercial_and_us_dropped(self) -> None:
        now = datetime.datetime(2026, 10, 26, 12, 0, tzinfo=datetime.timezone.utc)
        items = [
            # Commercial news (within 2 days, CBC) -> dropped
            {
                "title": "Apple launches new iPhone with Canadian carriers",
                "link": "https://www.cbc.ca/news/tech",
                "pub_date": "Sun, 25 Oct 2026 12:00:00 GMT",
                "summary": "Apple unveils latest mobile device in Canada.",
                "source": "CBC News",
            },
            # US domestic news -> dropped
            {
                "title": "Trump and Harris debate White House border strategy in Texas",
                "link": "https://www.cbc.ca/news/us",
                "pub_date": "Sun, 25 Oct 2026 12:00:00 GMT",
                "summary": "Capitol Hill leaders respond to Florida rally.",
                "source": "CBC News",
            },
            # Valid Canada immigration news -> selected!
            {
                "title": "Ontario adjusts work permit pathways for Indian and Chinese students",
                "link": "https://www.theglobeandmail.com/news/123",
                "pub_date": "Sun, 25 Oct 2026 10:00:00 GMT",
                "summary": "Provincial government updates regulations for international students.",
                "source": "The Globe and Mail",
            },
        ]
        result = select_best_news(items, now=now, max_age_days=2)
        self.assertIsNotNone(result)
        assert result is not None
        best_item, _, _ = result
        self.assertEqual(
            best_item["title"],
            "Ontario adjusts work permit pathways for Indian and Chinese students",
        )

    def test_format_relative_time(self) -> None:
        now = datetime.datetime(2026, 10, 26, 12, 0, tzinfo=datetime.timezone.utc)
        dt_1h = datetime.datetime(2026, 10, 26, 10, 0, tzinfo=datetime.timezone.utc)
        self.assertIn("2 小时前", format_relative_time(dt_1h, now=now))

        dt_1d = datetime.datetime(2026, 10, 25, 10, 0, tzinfo=datetime.timezone.utc)
        self.assertIn("1 天前", format_relative_time(dt_1d, now=now))

    def test_format_news_block(self) -> None:
        news = NewsItem(
            title="Smith scores slim majority on immigration questions",
            source="CBC News（加拿大广播公司）",
            url="https://www.cbc.ca/news/alberta-123",
            published_at=datetime.datetime(2026, 10, 25, 15, 40, tzinfo=datetime.timezone.utc),
            summary="Alberta referendum details.",
            zh_title="史密斯在移民问题上获得微弱多数支持",
            zh_summary="阿尔伯塔省公投结果出炉。",
            is_immigration=True,
        )
        block = format_news_block(news)
        self.assertIn("🍁 今日加拿大要闻（移民与新居民焦点）", block)
        self.assertIn("📌 标题：史密斯在移民问题上获得微弱多数支持", block)
        self.assertIn("🏷️ 原文：Smith scores slim majority on immigration questions", block)
        self.assertIn("🏛️ 来源：CBC News（加拿大广播公司）", block)
        self.assertIn("🔗 链接：https://www.cbc.ca/news/alberta-123", block)
        self.assertIn("📝 摘要：阿尔伯塔省公投结果出炉。", block)

    @patch("hoyolab_checkin.news.requests.get")
    def test_translate_to_zh_mocked(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [[["测试中文翻译", "Test English text"]]]
        mock_get.return_value = mock_resp

        res = translate_to_zh("Test English text")
        self.assertEqual(res, "测试中文翻译")

    @patch("hoyolab_checkin.news.requests.get")
    def test_fetch_daily_news_mocked(self, mock_get: MagicMock) -> None:
        sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Changes to Express Entry for high-wage occupations</title>
                    <link>https://www.canada.ca/en/news/ircc-express-entry.html</link>
                    <pubDate>Sun, 25 Oct 2026 12:00:00 GMT</pubDate>
                    <description>IRCC announced new categories for Express Entry candidates.</description>
                    <source>IRCC</source>
                </item>
            </channel>
        </rss>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_rss
        mock_resp.json.return_value = [[["高薪职位快速通道 Express Entry 迎来调整", "..."]]]
        mock_get.return_value = mock_resp

        now = datetime.datetime(2026, 10, 26, 12, 0, tzinfo=datetime.timezone.utc)
        news = fetch_daily_news(now=now, feed_urls=[("https://mock.feed/rss", "IRCC")])
        self.assertIsNotNone(news)
        assert news is not None
        self.assertEqual(news.title, "Changes to Express Entry for high-wage occupations")
        self.assertTrue(news.is_immigration)
        self.assertIn("IRCC", news.source)


if __name__ == "__main__":
    unittest.main()
