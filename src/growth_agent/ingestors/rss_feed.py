"""
RSS feed fetcher for ingesting articles from subscribed feeds.

This module uses feedparser to fetch and parse RSS/Atom feeds.
"""

import logging
from datetime import datetime, UTC
from typing import Any

import feedparser
import httpx

from growth_agent.config import Settings
from growth_agent.core.schema import RSSInboxItem

logger = logging.getLogger(__name__)


class RSSIngestor:
    """
    RSS feed ingestor for fetching articles.

    Supports RSS and Atom formats.
    """

    def __init__(self, settings: Settings):
        """
        Initialize RSS ingestor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        # HTTP client for fetching feeds
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def fetch_feed_items(
        self,
        feed_url: str,
        feed_id: str,
        feed_title: str,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[RSSInboxItem]:
        """
        Fetch articles from an RSS feed.

        Args:
            feed_url: URL of the RSS feed
            feed_id: Feed ID in the database
            feed_title: Title of the feed
            since: Optional datetime to filter articles after
            limit: Maximum number of articles to fetch

        Returns:
            List of RSSInboxItem objects
        """
        items = []

        try:
            # Fetch feed
            response = self.client.get(feed_url)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            # Check for errors
            if feed.get("bozo") and feed.get("bozo_exception"):
                logger.warning(f"Feed parsing warning for {feed_title}: {feed['bozo_exception']}")

            # Extract feed metadata
            feed_author = feed.get("feed", {}).get("title", feed_title)

            # Get max items from settings if limit not provided
            if limit is None:
                limit = self.settings.max_items_per_source

            # Process entries (with limit)
            entries = feed.get("entries", [])[:limit] if limit else feed.get("entries", [])

            for entry in entries:
                try:
                    item = self._parse_entry(entry, feed_id, feed_title, feed_author, since)
                    if item:
                        items.append(item)
                        # Stop if we've reached the limit
                        if limit and len(items) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")
                    continue

            logger.info(f"Fetched {len(items)} articles from {feed_title}")
            return items

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching feed {feed_title}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching feed {feed_title}: {e}")
            return []

    def _parse_entry(
        self,
        entry: dict[str, Any],
        feed_id: str,
        feed_title: str,
        feed_author: str,
        since: datetime | None = None,
    ) -> RSSInboxItem | None:
        """
        Parse a feed entry into RSSInboxItem.

        Args:
            entry: Feedparser entry
            feed_id: Feed ID
            feed_title: Feed title
            feed_author: Feed author name
            since: Optional datetime filter

        Returns:
            RSSInboxItem or None if filtered out
        """
        # Extract basic fields
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = entry.get("link", "")

        # Title
        title = entry.get("title", "")

        # Content (try content, then summary, then description)
        content = ""
        if "content" in entry:
            content_list = entry.get("content", [])
            if content_list and isinstance(content_list, list):
                content = content_list[0].get("value", "")
        if not content:
            content = entry.get("summary", entry.get("description", ""))

        # Strip HTML tags
        import re

        content = re.sub(r"<[^>]+>", "", content)
        content = content.strip()

        if not content:
            logger.warning(f"Entry {entry_id} has no content, skipping")
            return None

        # URL
        url = entry.get("link", "")

        # Published date
        published_parsed = entry.get("published_parsed")
        if published_parsed:
            published_at = datetime(*published_parsed[:6], tzinfo=UTC)
        else:
            # Fallback to updated date
            updated_parsed = entry.get("updated_parsed")
            if updated_parsed:
                published_at = datetime(*updated_parsed[:6], tzinfo=UTC)
            else:
                # Use current time
                published_at = datetime.now(UTC)

        # Filter by date if since is provided
        if since and published_at <= since:
            return None

        # Author
        author = entry.get("author", feed_author)

        # Categories/tags
        categories = []
        for tag in entry.get("tags", []):
            tag_term = tag.get("term", "")
            if tag_term:
                categories.append(tag_term)

        # Excerpt
        excerpt = entry.get("summary", "")[:500]

        return RSSInboxItem(
            original_id=entry_id,
            author_id=feed_id,
            author_name=author,
            title=title,
            content=content,
            url=url,
            published_at=published_at,
            feed_id=feed_id,
            feed_title=feed_title,
            categories=categories,
            excerpt=excerpt,
        )

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
