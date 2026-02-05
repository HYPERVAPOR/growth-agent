#!/usr/bin/env python
"""
Seed sample subscriptions for testing.

This script adds sample X creators and RSS feeds for testing purposes.
"""

import json
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4


def seed_subscriptions(data_root: Path = Path("data")) -> None:
    """Seed sample subscriptions for testing."""
    print("Seeding sample subscriptions...")

    # Sample X creators
    x_creators = [
        {
            "id": "1234567890",
            "username": "sample_user",
            "followers_count": 10000,
            "subscribed_at": datetime.now(UTC).isoformat(),
            "last_fetched_at": None,
        },
    ]

    # Sample RSS feeds
    rss_feeds = [
        {
            "id": str(uuid4()),
            "url": "https://example.com/feed.xml",
            "title": "Example Tech Blog",
            "category": "technology",
            "language": "en",
            "update_frequency": "daily",
            "subscribed_at": datetime.now(UTC).isoformat(),
            "last_fetched_at": None,
            "status": "active",
        },
        {
            "id": str(uuid4()),
            "url": "https://planet.python.org/rss20.xml",
            "title": "Planet Python",
            "category": "programming",
            "language": "en",
            "update_frequency": "daily",
            "subscribed_at": datetime.now(UTC).isoformat(),
            "last_fetched_at": None,
            "status": "active",
        },
    ]

    # Write to files
    x_creators_path = data_root / "subscriptions" / "x_creators.jsonl"
    rss_feeds_path = data_root / "subscriptions" / "rss_feeds.jsonl"

    # Append sample data
    with open(x_creators_path, "a") as f:
        for creator in x_creators:
            f.write(json.dumps(creator, ensure_ascii=False) + "\n")

    with open(rss_feeds_path, "a") as f:
        for feed in rss_feeds:
            f.write(json.dumps(feed, ensure_ascii=False) + "\n")

    print(f"  ✓ Added {len(x_creators)} X creator(s)")
    print(f"  ✓ Added {len(rss_feeds)} RSS feed(s)")

    print("\nSample subscriptions added!")
    print("\nNote: These are sample subscriptions for testing.")
    print("Edit the JSONL files to add real subscriptions.")


if __name__ == "__main__":
    seed_subscriptions()
