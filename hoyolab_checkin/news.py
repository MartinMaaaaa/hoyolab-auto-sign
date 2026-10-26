"""Daily Canadian news fetcher and filter for scheduled tasks."""
from __future__ import annotations

import datetime
import email.utils
import json
import logging
import re
import urllib.parse
from dataclasses import dataclass
from typing import Mapping, Sequence
import xml.etree.ElementTree as ET

import requests

from .config import Config

logger = logging.getLogger(__name__)

# Authority names and domain whitelist for official and high-weight media
AUTHORITATIVE_MEDIA_WHITELIST = (
    "IRCC",
    "Immigration, Refugees and Citizenship Canada",
    "Canada.ca",
    "CBC",
    "CBC News",
    "Radio-Canada",
    "The Globe and Mail",
    "Global News",
    "Toronto Star",
    "CTV News",
    "National Post",
)

AUTHORITATIVE_DOMAINS = (
    "canada.ca",
    "cbc.ca",
    "radio-canada.ca",
    "theglobeandmail.com",
    "globalnews.ca",
    "thestar.com",
    "ctvnews.ca",
    "nationalpost.com",
)

MEDIA_DISPLAY_NAMES: Mapping[str, str] = {
    "cbc": "CBC News（加拿大广播公司）",
    "cbc news": "CBC News（加拿大广播公司）",
    "radio-canada": "Radio-Canada（加拿大广播电台）",
    "the globe and mail": "The Globe and Mail（环球邮报）",
    "ircc": "IRCC（加拿大移民、难民及公民部官方）",
    "immigration, refugees and citizenship canada": "IRCC（加拿大移民部官方）",
    "canada.ca": "加拿大联邦政府官方 (Canada.ca)",
    "global news": "Global News（环球新闻）",
    "toronto star": "Toronto Star（多伦多星报）",
    "ctv news": "CTV News（加拿大电视网）",
    "national post": "National Post（国家邮报）",
}

# High-priority immigration, newcomer, diaspora & foreigner keywords
IMMIGRATION_KEYWORDS = (
    "immigrat", "newcomer", "refugee", "asylum", "foreign worker", "tfw",
    "study permit", "work permit", "permanent residen", "express entry", "citizenship",
    "deport", "border", "migrant", "chinese in canada", "indian in canada",
    "indo-canadian", "chinese canadian", "asian canadian", "south asian", "diaspora",
    "visa", "pr status", "international student", "international students",
    "undocumented", "naturalization", "settlement services", "foreign national",
    "中国人", "华人", "华裔", "印度人", "印裔", "留学生", "新移民", "外籍工人", "工签", "学签", "枫叶卡"
)

# Commercial news patterns to strictly reject (e.g., company product releases, earnings, stocks)
COMMERCIAL_PATTERNS = (
    r"\b(?:launches|unveils|releases|introduces)\s+(?:new|its\s+new|latest)\b",
    r"\b(?:company|corporation|inc|corp)\s+(?:launches|unveils|releases|introduces|announces)\b",
    r"\b(?:product|phone|chip|suv|vehicle|gadget)\s+launch\b",
    r"\b(?:q[1-4]\s+)?earnings\b",
    r"\bquarterly\s+(?:results|profit|revenue|loss)\b",
    r"\bshares\s+(?:rise|fall|drop|surge|plunge|jump)\b",
    r"\bstock\s+(?:price|jump|drop|surge)\b",
    r"\bmarket\s+capitalization\b",
    r"\binitial\s+public\s+offering\b",
    r"\bipo\b",
    r"\bmerger\b",
    r"\bacquisition\b",
    r"\bdiscounts?\b",
    r"\bpromo(?:tion)?s?\b",
    r"(?:公司|企业|厂商|集团)(?:发布|推出|宣布|上线)",
    r"(?:发布|推出|上线)(?:了)?(?:最新|全新|新一代)?(?:产品|新品|功能|服务|车型|系统|平台|芯片|旗舰)",
    r"财报",
    r"季度业绩",
    r"净利润",
    r"营业收入",
    r"股价(?:上涨|大跌|暴跌|飙升|走低|重挫)",
    r"完成(?:天使轮|A轮|B轮|Pre-IPO)?融资",
)

# US domestic news indicators
US_DOMESTIC_PATTERNS = (
    r"\bwhite\s+house\b", r"\bcapitol\s+hill\b", r"\bcongress\b", r"\bsenate\b",
    r"\bgop\b", r"\bdemocrats\b", r"\bus\s+election\b", r"\bflorida\b",
    r"\btexas\b", r"\bcalifornia\b", r"\bpentagon\b", r"\bmar-a-lago\b",
    r"\btrump\b", r"\bbiden\b", r"\bharris\b"
)

# Mandatory Canadian context keywords
CANADA_CONTEXT_KEYWORDS = (
    "canada", "canadian", "ottawa", "ontario", "british columbia", "b.c.",
    "alberta", "quebec", "calgary", "edmonton", "toronto", "vancouver",
    "montreal", "winnipeg", "saskatchewan", "nova scotia", "new brunswick",
    "ircc", "rcmp", "parliament", "house of commons", "premier", "federal government",
    "canadians", "枫叶国", "加拿大", "温哥华", "多伦多", "渥太华", "蒙特利尔", "卡尔加里"
)

DEFAULT_FEED_URLS = (
    # 1. Google News Query targeting Canadian authoritative media + immigration / newcomers
    (
        "https://news.google.com/rss/search?q="
        "when:2d+Canada+(immigration+OR+immigrant+OR+newcomers+OR+refugees+OR+%22foreign+workers%22+"
        "OR+%22international+students%22+OR+citizenship+OR+visa+OR+Chinese+OR+Indian)+"
        "(site:cbc.ca+OR+site:theglobeandmail.com+OR+site:canada.ca+OR+site:globalnews.ca+OR+site:ctvnews.ca+OR+site:torontostar.com)"
        "&hl=en-CA&gl=CA&ceid=CA:en",
        "Google News Canada",
    ),
    # 2. Official IRCC Atom Feed
    (
        "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentofcitizenshipandimmigration&sort=publishedDate&orderBy=desc&format=atom",
        "IRCC",
    ),
    # 3. CBC Canada News RSS
    (
        "https://www.cbc.ca/webfeed/rss/rss-canada",
        "CBC News",
    ),
    # 4. The Globe and Mail Canada RSS
    (
        "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/canada/",
        "The Globe and Mail",
    ),
    # 5. Global News Canada RSS
    (
        "https://globalnews.ca/canada/feed/",
        "Global News",
    ),
)


@dataclass(frozen=True, slots=True)
class NewsItem:
    """Parsed and validated news item meeting all criteria."""

    title: str
    source: str
    url: str
    published_at: datetime.datetime
    summary: str = ""
    zh_title: str | None = None
    zh_summary: str | None = None
    is_immigration: bool = False


def clean_text(raw_html: str) -> str:
    """Remove HTML tags, decode entities, and normalize whitespace."""
    clean = re.sub(r"<[^>]+>", " ", raw_html or "")
    clean = clean.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    clean = clean.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", clean).strip()


def parse_feed_date(date_str: str | None) -> datetime.datetime | None:
    """Parse feed date string from RFC 2822 or ISO 8601 into UTC datetime."""
    if not date_str:
        return None
    date_str = date_str.strip()

    # RFC 2822 (RSS standard)
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except Exception:
        pass

    # ISO 8601 (Atom standard)
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except Exception:
        pass

    return None


def is_authoritative_source(source_name: str, url: str) -> bool:
    """Verify that source or domain is within authoritative Canadian media whitelist."""
    source_lower = source_name.lower()
    url_lower = url.lower()

    for auth in AUTHORITATIVE_MEDIA_WHITELIST:
        if auth.lower() in source_lower:
            return True

    for domain in AUTHORITATIVE_DOMAINS:
        if domain in url_lower:
            return True

    return False


def get_display_source(source_name: str) -> str:
    """Map source name to human-readable authoritative display name."""
    s_lower = source_name.lower().strip()
    for key, display in MEDIA_DISPLAY_NAMES.items():
        if key in s_lower:
            return display
    return source_name


def is_commercial(text: str) -> bool:
    """Check if content matches commercial product release or corporate PR patterns."""
    for pat in COMMERCIAL_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def is_canada_related(text: str, source: str = "") -> bool:
    """Check if content is Canada-related and filter out US domestic news."""
    t = text.lower()
    s = source.lower()

    has_canada = any(k in t for k in CANADA_CONTEXT_KEYWORDS) or "canada" in s or "canadian" in s
    if not has_canada:
        return False

    has_us_domestic = any(re.search(pat, t) for pat in US_DOMESTIC_PATTERNS)
    if has_us_domestic:
        canada_count = sum(len(re.findall(re.escape(k), t)) for k in CANADA_CONTEXT_KEYWORDS)
        us_count = sum(len(re.findall(pat, t)) for pat in US_DOMESTIC_PATTERNS)
        if us_count >= 2 and canada_count == 0:
            return False

    return True


def calculate_score(text: str, source: str) -> int:
    """Score article prioritizing immigration, newcomers, and diaspora/foreigners."""
    t = text.lower()
    score = sum(2 for k in IMMIGRATION_KEYWORDS if k in t)

    if "ircc" in t or "immigration" in source.lower():
        score += 5

    if any(k in t for k in ("chinese", "indian", "indo-canadian", "diaspora", "华人", "印度", "留学生")):
        score += 3

    return score


def parse_items_from_xml(xml_content: str, default_source: str = "") -> list[dict[str, str]]:
    """Parse both RSS items and Atom entries from XML content."""
    items: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml_content)
    except Exception as err:
        logger.debug("Failed to parse XML: %s", err)
        return items

    # Strip XML namespace prefixes
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    # RSS items
    for item_el in root.iter("item"):
        title = clean_text(item_el.findtext("title") or "")
        link = clean_text(item_el.findtext("link") or "")
        pub_date = clean_text(item_el.findtext("pubDate") or "")
        desc = clean_text(item_el.findtext("description") or "")
        source_el = item_el.find("source")
        source = clean_text(source_el.text) if source_el is not None and source_el.text else default_source
        if title:
            # Strip trailing source name from title if present (e.g. "... - CBC")
            clean_title = re.sub(r"\s+-\s+[^-]+$", "", title).strip()
            items.append({
                "title": clean_title,
                "link": link,
                "pub_date": pub_date,
                "summary": desc,
                "source": source or default_source,
            })

    # Atom entries
    for entry_el in root.iter("entry"):
        title = clean_text(entry_el.findtext("title") or "")
        link = ""
        link_el = entry_el.find("link")
        if link_el is not None:
            link = clean_text(link_el.attrib.get("href") or link_el.text or "")
        pub_date = clean_text(entry_el.findtext("published") or entry_el.findtext("updated") or "")
        desc = clean_text(entry_el.findtext("summary") or entry_el.findtext("content") or "")
        author_el = entry_el.find("author")
        source = default_source
        if author_el is not None:
            name_el = author_el.find("name")
            if name_el is not None and name_el.text:
                source = clean_text(name_el.text)
        if title:
            clean_title = re.sub(r"\s+-\s+[^-]+$", "", title).strip()
            items.append({
                "title": clean_title,
                "link": link,
                "pub_date": pub_date,
                "summary": desc,
                "source": source or default_source,
            })

    return items


def translate_to_zh(text: str, timeout: float = 4.0) -> str | None:
    """Translate English text to Simplified Chinese with multi-endpoint fallback."""
    if not text or not text.strip():
        return None
    cleaned = text.strip()

    # 1. Google Translate web endpoint
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q="
            + urllib.parse.quote(cleaned)
        )
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            translated = "".join([part[0] for part in data[0] if part and part[0]])
            if translated and translated.strip():
                return translated.strip()
    except Exception as err:
        logger.debug("Google translation skipped or failed: %s", err)

    # 2. MyMemory Translate fallback endpoint
    try:
        url = (
            "https://api.mymemory.translated.net/get?q="
            + urllib.parse.quote(cleaned)
            + "&langpair=en|zh-CN"
        )
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            res_data = resp.json().get("responseData", {})
            trans = res_data.get("translatedText", "")
            if trans and trans.strip() and trans.strip().lower() != cleaned.lower():
                return trans.strip()
    except Exception as err:
        logger.debug("MyMemory translation skipped or failed: %s", err)

    return None


def select_best_news(
    candidates: Sequence[dict[str, str]],
    now: datetime.datetime | None = None,
    max_age_days: int = 2,
) -> tuple[dict[str, str], datetime.datetime, int] | None:
    """Filter candidate items against the 4 requirements and return the top match."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    cutoff = now - datetime.timedelta(days=max_age_days)
    future_limit = now + datetime.timedelta(hours=2)

    valid_candidates: list[tuple[int, datetime.datetime, dict[str, str]]] = []
    seen_titles: set[str] = set()

    for item in candidates:
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        source = item.get("source", "").strip()
        summary = item.get("summary", "").strip()
        pub_date_str = item.get("pub_date", "")

        if not title or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        # Requirement 1: Must be within 2 days
        dt = parse_feed_date(pub_date_str)
        if dt is None or dt < cutoff or dt > future_limit:
            continue

        # Requirement 2: Must be from authoritative sources or official media
        if not is_authoritative_source(source, link):
            continue

        full_text = f"{title} {summary}"

        # Requirement 4: Strictly no commercial news
        if is_commercial(full_text):
            continue

        # Requirement 3: Must be Canada-related (filter US news)
        if not is_canada_related(full_text, source):
            continue

        # Score prioritizing immigration / newcomers / foreigners
        score = calculate_score(full_text, source)
        valid_candidates.append((score, dt, item))

    if not valid_candidates:
        return None

    # Sort descending by score, then by publication time
    valid_candidates.sort(key=lambda x: (x[0], x[1].timestamp()), reverse=True)
    best_score, best_dt, best_item = valid_candidates[0]
    return best_item, best_dt, best_score


def fetch_daily_news(
    config: Config | None = None,
    now: datetime.datetime | None = None,
    feed_urls: Sequence[tuple[str, str]] = DEFAULT_FEED_URLS,
) -> NewsItem | None:
    """Fetch, filter, and format the single top daily Canadian news update."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    all_raw_items: list[dict[str, str]] = []

    for url, default_src in feed_urls:
        try:
            logger.debug("Fetching feed: %s (%s)", default_src, url)
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=(6.0, 10.0),
            )
            if resp.status_code == 200 and resp.text:
                parsed = parse_items_from_xml(resp.text, default_src)
                all_raw_items.extend(parsed)
        except Exception as err:
            logger.debug("Failed to fetch feed '%s': %s", default_src, err)

    match = select_best_news(all_raw_items, now=now, max_age_days=2)
    if not match:
        return None

    item, pub_dt, score = match
    title = item["title"]
    source = get_display_source(item["source"])
    link = item["link"]
    summary = item.get("summary", "")
    is_immigration = score > 0

    # Translate title and summary into Chinese
    zh_title = translate_to_zh(title)
    zh_summary = translate_to_zh(summary) if summary else None

    return NewsItem(
        title=title,
        source=source,
        url=link,
        published_at=pub_dt,
        summary=summary,
        zh_title=zh_title,
        zh_summary=zh_summary,
        is_immigration=is_immigration,
    )


def format_relative_time(pub_dt: datetime.datetime, now: datetime.datetime | None = None) -> str:
    """Format publication date with relative time description."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    delta = now - pub_dt
    hours = max(0, int(delta.total_seconds() // 3600))
    if hours < 1:
        rel = "刚刚"
    elif hours < 24:
        rel = f"{hours} 小时前"
    else:
        days = hours // 24
        rel = f"{days} 天前"

    date_str = pub_dt.strftime("%Y-%m-%d %H:%M UTC")
    return f"{date_str}（{rel}）"


def format_news_block(news: NewsItem) -> str:
    """Format NewsItem into an informative notification text block."""
    category = "🍁 今日加拿大要闻（移民与新居民焦点）" if news.is_immigration else "🍁 今日加拿大要闻"
    title_line = news.zh_title if news.zh_title else news.title
    rel_time = format_relative_time(news.published_at)

    lines = [
        "━━━━━━━━━━━━━━━━━━",
        f"📰 {category}",
        f"📌 标题：{title_line}",
    ]

    if news.zh_title and news.zh_title != news.title:
        lines.append(f"🏷️ 原文：{news.title}")

    lines.append(f"🏛️ 来源：{news.source}")
    lines.append(f"🕒 发布：{rel_time}")
    lines.append(f"🔗 链接：{news.url}")

    summary_text = news.zh_summary if news.zh_summary else news.summary
    if summary_text:
        # Truncate summary if excessively long
        if len(summary_text) > 150:
            summary_text = summary_text[:147] + "..."
        lines.append(f"📝 摘要：{summary_text}")

    lines.append("━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
