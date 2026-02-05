"""
Deduplication utilities for content ingestion.

This module provides functions to prevent duplicate content in the database.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """
    Track seen content to prevent duplicates.
    """

    def __init__(self):
        """Initialize deduplicator with empty seen set."""
        # Track seen content by source and original_id
        self.seen_items: set[tuple[str, str]] = set()

    def is_duplicate(self, source: str, original_id: str) -> bool:
        """
        Check if content has already been seen.

        Args:
            source: Content source (x/rss)
            original_id: Original content ID from the platform

        Returns:
            True if this content has been seen before, False otherwise
        """
        key = (source, original_id)
        is_dup = key in self.seen_items

        if not is_dup:
            self.seen_items.add(key)

        return is_dup

    def filter_duplicates(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter out duplicate items from a list.

        Args:
            items: List of inbox item dictionaries

        Returns:
            List with duplicates removed
        """
        seen_in_batch: set[tuple[str, str]] = set()
        unique_items = []

        for item in items:
            key = (item.get("source"), item.get("original_id"))

            if key not in self.seen_items and key not in seen_in_batch:
                self.seen_items.add(key)
                seen_in_batch.add(key)
                unique_items.append(item)
            else:
                logger.debug(f"Filtered duplicate: {item.get('source')}/{item.get('original_id')}")

        logger.info(f"Filtered {len(items) - len(unique_items)} duplicates")
        return unique_items

    def mark_as_seen(self, items: list[dict[str, Any]]) -> None:
        """
        Mark items as seen without storing them.

        Args:
            items: List of inbox item dictionaries
        """
        for item in items:
            key = (item.get("source"), item.get("original_id"))
            self.seen_items.add(key)

    def reset(self) -> None:
        """Clear all seen items."""
        self.seen_items.clear()
        logger.info("Deduplicator reset")
