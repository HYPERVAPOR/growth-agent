"""
Content ranker for filtering and sorting curated items.

This module filters items by score threshold and ranks top K items.
"""

import logging
from typing import Any

from growth_agent.core.schema import CuratedItem

logger = logging.getLogger(__name__)


class ContentRanker:
    """
    Filter and rank curated content by score.
    """

    def filter_and_rank(
        self,
        curated_items: list[CuratedItem],
        min_score: int = 60,
        top_k: int = 10,
    ) -> list[CuratedItem]:
        """
        Filter by score and return top K items.

        Args:
            curated_items: List of curated items with scores
            min_score: Minimum score threshold (0-100)
            top_k: Maximum number of items to return

        Returns:
            Ranked list of curated items (descending by score)
        """
        # Step 1: Filter by score threshold
        qualified = [item for item in curated_items if item.score >= min_score]

        logger.info(
            f"Score filtering: {len(qualified)}/{len(curated_items)} items "
            f"met threshold (score >= {min_score})"
        )

        if not qualified:
            logger.warning("No items met the score threshold")
            return []

        # Step 2: Sort by score (descending)
        ranked = sorted(qualified, key=lambda x: x.score, reverse=True)

        # Step 3: Take top K
        top_items = ranked[:top_k]

        # Step 4: Assign ranks
        for idx, item in enumerate(top_items, start=1):
            item.rank = idx

        logger.info(
            f"Ranking complete: returned top {len(top_items)} items "
            f"(score range: {top_items[0].score} - {top_items[-1].score})"
        )

        return top_items

    def get_statistics(self, items: list[CuratedItem]) -> dict[str, Any]:
        """
        Calculate statistics for curated items.

        Args:
            items: List of curated items

        Returns:
            Dictionary with statistics
        """
        if not items:
            return {
                "total": 0,
                "avg_score": 0.0,
                "max_score": 0,
                "min_score": 0,
            }

        scores = [item.score for item in items]

        return {
            "total": len(items),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "score_distribution": {
                "90-100": len([s for s in scores if s >= 90]),
                "75-89": len([s for s in scores if 75 <= s < 90]),
                "60-74": len([s for s in scores if 60 <= s < 75]),
                "0-59": len([s for s in scores if s < 60]),
            },
        }
