"""
Content curator using LLM for evaluation and scoring.

This module evaluates inbox items and generates curated content with scores.
"""

import logging
from typing import Any

from growth_agent.core.llm import LLMClient
from growth_agent.core.schema import ContentEvaluation, CuratedItem

logger = logging.getLogger(__name__)


class ContentCurator:
    """
    LLM-based content curator.

    Evaluates content quality and generates summaries and comments.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize content curator.

        Args:
            llm_client: LLM client for evaluation
        """
        self.llm = llm_client

    def evaluate_items(self, items: list[dict[str, Any]]) -> list[CuratedItem]:
        """
        Batch evaluate inbox items using LLM.

        Args:
            items: List of inbox item dictionaries

        Returns:
            List of CuratedItem with scores, summaries, and comments
        """
        curated_items = []

        for item in items:
            try:
                # Evaluate content
                evaluation = self.llm.evaluate_content(
                    content=item.get("content", ""),
                    author=item.get("author_name", ""),
                    source=item.get("source", ""),
                )

                # Create curated item with original fields preserved
                curated_item = CuratedItem(
                    source_id=item.get("id"),
                    score=evaluation.score,
                    summary=evaluation.summary,
                    comment=evaluation.comment,
                    # Preserve original content fields
                    url=item.get("url", ""),
                    author_name=item.get("author_name", ""),
                    title=item.get("title"),
                    content=item.get("content", ""),
                    published_at=item.get("published_at"),
                    source=item.get("source", ""),
                )

                curated_items.append(curated_item)

                logger.debug(f"Evaluated item {item.get('id')}: score={evaluation.score}")

            except Exception as e:
                logger.error(f"Evaluation failed for item {item.get('id')}: {e}")
                # Continue with other items
                continue

        logger.info(f"Evaluated {len(curated_items)}/{len(items)} items successfully")
        return curated_items

    def evaluate_items_batch(
        self,
        items: list[dict[str, Any]],
        batch_size: int = 5,
    ) -> list[CuratedItem]:
        """
        Evaluate items in batches with progress tracking.

        Args:
            items: List of inbox item dictionaries
            batch_size: Number of items to process before logging progress

        Returns:
            List of CuratedItem with scores, summaries, and comments
        """
        total_items = len(items)
        curated_items = []

        for i in range(0, total_items, batch_size):
            batch = items[i : i + batch_size]
            batch_results = self.evaluate_items(batch)
            curated_items.extend(batch_results)

            # Log progress
            processed = min(i + batch_size, total_items)
            logger.info(f"Progress: {processed}/{total_items} items evaluated")

        return curated_items
