"""
X/Twitter API client for fetching creator tweets.

This module uses RapidAPI to fetch tweets from subscribed X creators.
"""

import logging
from datetime import datetime, UTC
from typing import Any

import httpx

from growth_agent.config import Settings
from growth_agent.core.schema import XInboxItem

logger = logging.getLogger(__name__)


class XTwitterIngestor:
    """
    X/Twitter API client for fetching tweets from creators.

    Uses RapidAPI's Twitter API v2 endpoint.
    """

    def __init__(self, settings: Settings):
        """
        Initialize X/Twitter ingestor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = f"https://{settings.x_rapidapi_host}"
        self.headers = settings.get_x_api_headers()

        # HTTP client with timeout
        self.client = httpx.Client(timeout=30.0)

    def fetch_creator_tweets(
        self,
        creator_id: str,
        username: str,
        count: int = 20,
        since_id: str | None = None,
    ) -> list[XInboxItem]:
        """
        Fetch recent tweets from a creator.

        Args:
            creator_id: X user ID (numeric string)
            username: X username (without @)
            count: Number of tweets to fetch (max 100)
            since_id: Optional tweet ID to fetch tweets after

        Returns:
            List of XInboxItem objects
        """
        url = f"{self.base_url}/user-tweets"
        params = {"user": creator_id, "count": str(count)}

        if since_id:
            params["since_id"] = since_id

        items = []

        try:
            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse tweets from response
            # Note: Response structure depends on the specific RapidAPI endpoint
            tweets = self._extract_tweets(data)

            # Limit results to count (API may return more than requested)
            for tweet_data in tweets[:count]:
                try:
                    item = self._parse_tweet(tweet_data, username, creator_id)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse tweet: {e}")
                    continue

            logger.info(f"Fetched {len(items)} tweets from @{username}")
            return items

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching tweets from @{username}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching tweets from @{username}: {e}")
            return []

    def _extract_tweets(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract tweet list from API response.

        Args:
            data: API response data

        Returns:
            List of tweet dictionaries
        """
        tweets = []

        # Actual structure: result.timeline.instructions[].entries[].content.itemContent.tweet_results.result
        # OR: result.data.user.result.timeline_response.timeline.instructions

        # Try structure 1: result.timeline.instructions...
        if "result" in data:
            result = data["result"]
            if "timeline" in result:
                timeline = result["timeline"]
                if "instructions" in timeline:
                    instructions = timeline["instructions"]
                    for instruction in instructions:
                        if instruction.get("type") == "TimelineAddEntries":
                            entries = instruction.get("entries", [])
                            for entry in entries:
                                content = entry.get("content", {})
                                if content.get("entryType") == "TimelineTimelineItem":
                                    item_content = content.get("itemContent", {})
                                    if item_content.get("itemType") == "TimelineTweet":
                                        tweet_results = item_content.get("tweet_results", {})
                                        if "result" in tweet_results:
                                            tweets.append(tweet_results["result"])

        # Try structure 2: data.data.user.result.timeline_response...
        elif not tweets and "data" in data:
            inner_data = data["data"]
            if "user" in inner_data:
                user_data = inner_data["user"]
                if "result" in user_data:
                    result = user_data["result"]
                    if "timeline_response" in result:
                        timeline = result["timeline_response"]
                        if "timeline" in timeline:
                            instructions = timeline["timeline"].get("instructions", [])
                            for instruction in instructions:
                                if "entries" in instruction:
                                    for entry in instruction["entries"]:
                                        if "content" in entry:
                                            content = entry["content"]
                                            if "tweet_results" in content:
                                                result = content["tweet_results"]
                                                if "result" in result:
                                                    tweets.append(result["result"])

        logger.debug(f"Extracted {len(tweets)} tweets from response")
        return tweets

    def _parse_tweet(self, tweet_data: dict[str, Any], username: str, creator_id: str) -> XInboxItem:
        """
        Parse tweet data into XInboxItem.

        Args:
            tweet_data: Raw tweet data from API
            username: Username of the tweet author
            creator_id: User ID from subscription (as fallback)

        Returns:
            XInboxItem object
        """
        # Extract basic fields
        rest_id = tweet_data.get("rest_id", "")
        legacy = tweet_data.get("legacy", {})

        # Extract user ID - use creator_id (the account we fetched from)
        # This is more reliable than parsing from API response, especially for quoted tweets
        user_id_str = creator_id

        # Text content
        full_text = legacy.get("full_text", "")

        # Handle extended tweets
        if "extended_entities" in legacy:
            media = []
            for media_item in legacy.get("extended_entities", {}).get("media", []):
                media_url = media_item.get("media_url_https", "")
                if media_url:
                    media.append(media_url)
        else:
            media = []

        # Hashtags
        hashtags = []
        for hashtag in legacy.get("entities", {}).get("hashtags", []):
            tag = hashtag.get("text", "")
            if tag:
                hashtags.append(tag)

        # Metrics
        favorite_count = legacy.get("favorite_count", 0)
        retweet_count = legacy.get("retweet_count", 0)
        reply_count = legacy.get("reply_count", 0)
        quote_count = legacy.get("quote_count", 0)

        # URLs
        urls = legacy.get("entities", {}).get("urls", [])
        tweet_url = f"https://twitter.com/{username}/status/{rest_id}"

        # Timestamp
        created_at = legacy.get("created_at", "")
        published_at = self._parse_twitter_date(created_at)

        return XInboxItem(
            original_id=rest_id,
            author_id=user_id_str,  # User ID from core.user_results.result.rest_id
            author_name=username,
            content=full_text,
            url=tweet_url,
            published_at=published_at,
            username=username,
            reply_count=reply_count,
            retweet_count=retweet_count,
            like_count=favorite_count,
            quote_count=quote_count,
            media=media,
            hashtags=hashtags,
        )

    def _parse_twitter_date(self, date_str: str) -> datetime:
        """
        Parse Twitter date string to datetime.

        Twitter format: "Wed Jan 01 00:00:00 +0000 2026"

        Args:
            date_str: Twitter date string

        Returns:
            datetime object
        """
        try:
            # Parse Twitter date format
            return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y").astimezone(UTC)
        except Exception:
            # Fallback to current time
            logger.warning(f"Failed to parse date: {date_str}, using current time")
            return datetime.now(UTC)

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
