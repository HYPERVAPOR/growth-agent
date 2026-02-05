"""
Social media metrics collector for X/Twitter and LinkedIn.

Fetches engagement metrics (impressions, likes, retweets, etc.) for tracking.
"""

import logging
from datetime import datetime, UTC
from typing import Any

import httpx

from growth_agent.config import Settings
from growth_agent.core.schema import MetricStat
from growth_agent.ingestors.x_twitter import XTwitterIngestor

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Social media metrics collector.

    Fetches engagement metrics from X/Twitter using RapidAPI.
    """

    def __init__(self, settings: Settings):
        """
        Initialize metrics collector.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = f"https://{settings.x_rapidapi_host}"
        self.headers = settings.get_x_api_headers()

        # HTTP client with timeout
        self.client = httpx.Client(timeout=30.0)

        # Reuse XTwitterIngestor for fetching tweets
        self.x_ingestor = XTwitterIngestor(settings)

    def fetch_user_tweets_metrics(
        self,
        username: str,
        user_id: str,
        count: int = 20,
    ) -> list[MetricStat]:
        """
        Fetch metrics for recent tweets from a user.

        Args:
            username: X username (without @)
            user_id: X user ID (numeric string)
            count: Number of recent tweets to fetch metrics for

        Returns:
            List of MetricStat objects with engagement data
        """
        logger.info(f"Fetching metrics for @{username}'s recent tweets")

        metrics_list = []

        try:
            # Use XTwitterIngestor to fetch tweets
            tweets = self.x_ingestor.fetch_creator_tweets(
                creator_id=user_id,
                username=username,
                count=count,
            )

            # Extract metrics from each tweet
            for tweet in tweets:
                try:
                    # Calculate engagements (sum of all interactions)
                    engagements = tweet.reply_count + tweet.retweet_count + tweet.like_count + tweet.quote_count

                    # Use 0 as default (not None) for available metrics
                    metric = MetricStat(
                        platform="x",
                        content_type="post",
                        content_id=tweet.original_id,
                        url=tweet.url,
                        impressions=None,  # Not available in user-tweets endpoint
                        engagements=engagements if engagements > 0 else None,
                        likes=tweet.like_count if tweet.like_count > 0 else None,
                        retweets=tweet.retweet_count if tweet.retweet_count > 0 else None,
                        replies=tweet.reply_count if tweet.reply_count > 0 else None,
                        clicks=None,  # Not available
                    )
                    metrics_list.append(metric)
                except Exception as e:
                    logger.warning(f"Failed to extract metrics from tweet {tweet.original_id}: {e}")
                    continue

            logger.info(f"Fetched metrics for {len(metrics_list)} tweets from @{username}")
            return metrics_list

        except Exception as e:
            logger.error(f"Error fetching metrics for @{username}: {e}")
            return []

    def fetch_tweet_metrics(self, tweet_id: str, username: str, user_id: str) -> MetricStat | None:
        """
        Fetch engagement metrics for a specific tweet (not implemented).

        Args:
            tweet_id: Tweet ID
            username: Tweet author username
            user_id: Tweet author user ID

        Returns:
            MetricStat with engagement data or None
        """
        logger.warning("Fetching individual tweet metrics not yet implemented")
        return None

    def fetch_linkedin_metrics(self, post_id: str) -> MetricStat | None:
        """
        Fetch metrics for LinkedIn post (not yet implemented).

        Args:
            post_id: LinkedIn post ID

        Returns:
            MetricStat with engagement metrics
        """
        logger.warning("LinkedIn metrics collection not yet implemented")
        return None

    def get_user_id(self, username: str) -> str | None:
        """
        Get user ID from username using RapidAPI.

        Args:
            username: X username (without @)

        Returns:
            User ID as string or None if failed
        """
        logger.debug(f"Fetching user ID for @{username}")

        # Try multiple endpoints
        endpoints_to_try = [
            ("user-by-username", {"username": username}),
            ("user", {"username": username}),
            ("profile", {"screen_name": username}),
        ]

        for endpoint_name, params in endpoints_to_try:
            try:
                url = f"{self.base_url}/{endpoint_name}"
                logger.debug(f"Trying endpoint: {endpoint_name}")

                response = self.client.get(url, headers=self.headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Response from {endpoint_name}: {type(data)}")

                    # Extract user ID from various possible response structures
                    user_id = None

                    # Try different paths
                    if isinstance(data, dict):
                        user_id = (
                            data.get("data", {}).get("rest_id")
                            or data.get("data", {}).get("id")
                            or data.get("rest_id")
                            or data.get("id_str")
                            or data.get("id")
                        )
                    elif isinstance(data, list) and len(data) > 0:
                        user_id = (
                            data[0].get("data", {}).get("rest_id")
                            or data[0].get("rest_id")
                            or data[0].get("id_str")
                            or data[0].get("id")
                        )

                    if user_id:
                        logger.info(f"✓ Found user ID for @{username}: {user_id}")
                        return str(user_id)

            except Exception as e:
                logger.debug(f"Endpoint {endpoint_name} failed: {e}")
                continue

        logger.error(f"Could not fetch user ID for @{username} after trying all endpoints")
        return None
