from __future__ import annotations

import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any

import feedparser
import requests

from growth_agent.social_listener.models import ContentItem

logger = logging.getLogger(__name__)


class RSSFetcher:
    def __init__(self, timeout: int = 30, retries: int = 2):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                )
            }
        )

    def parse_config(self, config_path: Path) -> list[dict[str, Any]]:
        if config_path.suffix.lower() == ".opml":
            return self.parse_opml(config_path)
        if config_path.suffix.lower() == ".json":
            return self.parse_json_sources(config_path)
        raise ValueError("Config file must be .json or .opml")

    def parse_opml(self, opml_path: Path) -> list[dict[str, Any]]:
        tree = ET.parse(opml_path)
        root = tree.getroot()
        sources: list[dict[str, Any]] = []
        for outline in root.findall('.//outline[@type="rss"]'):
            sources.append(
                {
                    "name": outline.get("title", outline.get("text", "Unknown")),
                    "url": outline.get("xmlUrl"),
                    "type": "rss",
                }
            )
        return sources

    def parse_json_sources(self, json_path: Path) -> list[dict[str, Any]]:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        return payload.get("sources", [])

    def fetch_single_feed(self, source: dict[str, Any], hours_back: int) -> list[ContentItem]:
        url = source.get("url")
        name = source.get("name", "Unknown")
        if not url:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        items: list[ContentItem] = []

        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                feed = feedparser.parse(response.content)

                for entry in feed.entries:
                    pub_date = self._parse_date(entry)
                    if pub_date and pub_date < cutoff_time:
                        continue

                    content = self._extract_content(entry)
                    items.append(
                        ContentItem(
                            title=self._clean_text(entry.get("title", "")),
                            author=entry.get("author", name),
                            link=entry.get("link", ""),
                            content=content,
                            pub_date=pub_date or datetime.now(),
                            source=name,
                            content_type="twitter"
                            if "twitter" in url.lower() or "x.com" in url.lower()
                            else "rss",
                            raw_data=dict(entry),
                        )
                    )

                logger.info("Fetched %s items from %s", len(items), name)
                break
            except Exception as exc:
                logger.warning("Failed fetching %s (attempt %s): %s", name, attempt + 1, exc)
                if attempt < self.retries:
                    time.sleep(2**attempt)

        return items

    def fetch_all(self, sources: list[dict[str, Any]], hours_back: int) -> list[ContentItem]:
        all_items: list[ContentItem] = []
        for source in sources:
            all_items.extend(self.fetch_single_feed(source, hours_back))
            time.sleep(0.3)
        all_items.sort(key=lambda item: item.pub_date, reverse=True)
        return all_items

    def _parse_date(self, entry: Any) -> datetime | None:
        for field in ("published_parsed", "updated_parsed", "created_parsed"):
            value = getattr(entry, field, None)
            if value:
                try:
                    return datetime(*value[:6])
                except Exception:
                    continue

        for field in ("published", "updated", "pubDate"):
            value = entry.get(field, "")
            if not value:
                continue
            try:
                parsed = parsedate_to_datetime(value)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(tzinfo=None)
                return parsed
            except Exception:
                pass
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(tzinfo=None)
                return parsed
            except Exception:
                continue
        return None

    def _extract_content(self, entry: Any) -> str:
        content = ""
        if hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description
        elif hasattr(entry, "content"):
            content = entry.content[0].value if entry.content else ""

        content = unescape(self._strip_html(content))
        return self._clean_text(content)

    @staticmethod
    def _strip_html(text: str) -> str:
        return re.sub(r"<.*?>", "", text or "")

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        return " ".join(text.split()).strip()


class ContentFilter:
    def __init__(self, min_words: int = 10):
        self.min_words = min_words
        self.rt_pattern = re.compile(r"^RT\s+@\w+:", re.IGNORECASE)
        self.reply_pattern = re.compile(r"^@\w+\s+.{0,50}$")

    def filter(self, items: list[ContentItem]) -> list[ContentItem]:
        filtered: list[ContentItem] = []
        for item in items:
            if self._is_pure_retweet(item):
                continue
            if self._is_too_short(item):
                continue
            if self._is_social_reply(item):
                continue
            filtered.append(item)
        logger.info("Pre-filtered %s items to %s", len(items), len(filtered))
        return filtered

    def _is_pure_retweet(self, item: ContentItem) -> bool:
        content = item.content or item.title
        if not self.rt_pattern.match(content):
            return False
        parts = content.split("RT @", 1)
        return len(parts) == 2 and len(parts[0].strip()) < 5

    def _is_too_short(self, item: ContentItem) -> bool:
        return len((item.content or item.title).split()) < self.min_words

    def _is_social_reply(self, item: ContentItem) -> bool:
        content = item.content or item.title
        if self.reply_pattern.match(content):
            return True
        return any(
            re.match(pattern, content, re.IGNORECASE)
            for pattern in (
                r"^thanks?\s+@",
                r"^thank\s+you\s+@",
                r"^congrats?\s+@",
                r"^happy\s+\w+\s+@",
            )
        )
