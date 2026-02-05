"""
Workflow B: Content Intelligence & Blog Creation.

This module orchestrates the three-stage pipeline for content intelligence.
"""

import logging
from datetime import datetime, UTC
from typing import Any

from growth_agent.config import Settings
from growth_agent.core.llm import LLMClient
from growth_agent.core.schema import WorkflowResult
from growth_agent.core.storage import StorageManager
from growth_agent.core.vector_store import VectorStore
from growth_agent.ingestors.rss_feed import RSSIngestor
from growth_agent.ingestors.x_twitter import XTwitterIngestor
from growth_agent.processors.blog_generator import BlogGenerator
from growth_agent.processors.curator import ContentCurator
from growth_agent.processors.ranker import ContentRanker
from growth_agent.workflows.base import Workflow

logger = logging.getLogger(__name__)


class WorkflowB(Workflow):
    """
    Content Intelligence & Blog Creation workflow.

    Three-stage pipeline:
    1. Ingestion: Fetch from X and RSS sources
    2. Curation: LLM evaluation and filtering
    3. Generation: Blog post creation
    """

    def __init__(self, settings: Settings, storage: StorageManager):
        """
        Initialize Workflow B.

        Args:
            settings: Application settings
            storage: Storage manager instance
        """
        super().__init__(settings, storage)

        # Initialize ingestors
        self.x_ingestor = XTwitterIngestor(settings)
        self.rss_ingestor = RSSIngestor(settings)

        # Initialize processors
        self.llm_client = LLMClient(settings)
        self.curator = ContentCurator(self.llm_client)
        self.ranker = ContentRanker()
        self.blog_generator = BlogGenerator(self.llm_client)

        # Initialize vector store
        self.vector_store = VectorStore(settings, self.llm_client)

    def validate_prerequisites(self) -> bool:
        """
        Validate prerequisites for Workflow B.

        Checks:
        - API keys are configured
        - Subscription files exist

        Returns:
            True if all prerequisites are met
        """
        # Check API keys
        if not self.settings.x_rapidapi_key or self.settings.x_rapidapi_key == "your_key_here":
            logger.error("X RapidAPI key not configured")
            return False

        if not self.settings.openrouter_api_key or self.settings.openrouter_api_key == "sk-...":
            logger.error("OpenRouter API key not configured")
            return False

        # Check subscription files exist (or are empty)
        x_creators_path = self.storage.data_root / "subscriptions" / "x_creators.jsonl"
        rss_feeds_path = self.storage.data_root / "subscriptions" / "rss_feeds.jsonl"

        # Files don't need to exist, but should be creatable
        if not self.storage.data_root.exists():
            logger.error(f"Data root does not exist: {self.storage.data_root}")
            return False

        logger.info("Workflow B prerequisites validated")
        return True

    def execute(self) -> WorkflowResult:
        """
        Execute the three-stage pipeline.

        Returns:
            WorkflowResult with execution details
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Workflow B: Content Intelligence")
        self.logger.info("=" * 60)

        # Stage 1: Ingestion
        ingestion_result = self._run_ingestion()
        if not ingestion_result.success:
            return ingestion_result

        # Stage 2: Curation
        curation_result = self._run_curation()
        if not curation_result.success:
            return curation_result

        # Stage 3: Generation
        generation_result = self._run_generation()
        if not generation_result.success:
            return generation_result

        # Combine results
        final_result = WorkflowResult(
            success=True,
            items_processed=(
                ingestion_result.items_processed
                + curation_result.items_processed
                + generation_result.items_processed
            ),
            metadata={
                "ingestion": ingestion_result.metadata,
                "curation": curation_result.metadata,
                "generation": generation_result.metadata,
            },
        )

        self.logger.info("=" * 60)
        self.logger.info(f"Workflow B completed successfully")
        self.logger.info(f"  Ingested: {ingestion_result.items_processed} items")
        self.logger.info(f"  Curated: {curation_result.items_processed} items")
        self.logger.info(f"  Generated: {generation_result.items_processed} blogs")
        self.logger.info("=" * 60)

        return final_result

    def _run_ingestion(self) -> WorkflowResult:
        """
        Stage 1: Fetch from X and RSS sources.

        Returns:
            WorkflowResult with ingestion details
        """
        self.logger.info("Stage 1: Ingestion - Fetching from sources")

        fetched_items = []
        errors = []

        # Fetch from X creators
        x_creators = self.storage.read_x_creators()
        self.logger.info(f"Found {len(x_creators)} X creator subscriptions")

        for creator in x_creators:
            try:
                creator_id = creator.get("id")
                username = creator.get("username")
                last_fetched = creator.get("last_fetched_at")

                # Convert last_fetched to datetime if needed
                since = None
                if last_fetched:
                    if isinstance(last_fetched, str):
                        since = datetime.fromisoformat(last_fetched.replace("Z", "+00:00"))
                    else:
                        since = last_fetched

                items = self.x_ingestor.fetch_creator_tweets(
                    creator_id=creator_id,
                    username=username,
                    count=self.settings.max_items_per_source,
                    since_id=None,  # Always fetch recent tweets
                )

                fetched_items.extend([item.model_dump() for item in items])

                # Update last_fetched_at
                self.storage.jsonl.update_field(
                    "subscriptions/x_creators.jsonl",
                    "id",
                    creator_id,
                    "last_fetched_at",
                    datetime.now(UTC).isoformat(),
                )

                self.logger.info(f"Fetched {len(items)} tweets from @{username}")

            except Exception as e:
                error_msg = f"Failed to fetch from @{creator.get('username')}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Fetch from RSS feeds
        rss_feeds = self.storage.read_rss_feeds()
        self.logger.info(f"Found {len(rss_feeds)} RSS feed subscriptions")

        for feed in rss_feeds:
            try:
                feed_id = feed.get("id")
                feed_url = feed.get("url")
                feed_title = feed.get("title")
                last_fetched = feed.get("last_fetched_at")

                # Convert last_fetched to datetime if needed
                since = None
                if last_fetched:
                    if isinstance(last_fetched, str):
                        since = datetime.fromisoformat(last_fetched.replace("Z", "+00:00"))
                    else:
                        since = last_fetched

                items = self.rss_ingestor.fetch_feed_items(
                    feed_url=feed_url,
                    feed_id=feed_id,
                    feed_title=feed_title,
                    since=since,
                    limit=self.settings.max_items_per_source,
                )

                fetched_items.extend([item.model_dump() for item in items])

                # Update last_fetched_at
                self.storage.jsonl.update_field(
                    "subscriptions/rss_feeds.jsonl",
                    "id",
                    feed_id,
                    "last_fetched_at",
                    datetime.now(UTC).isoformat(),
                )

                self.logger.info(f"Fetched {len(items)} articles from {feed_title}")

            except Exception as e:
                error_msg = f"Failed to fetch from {feed.get('title')}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Write to inbox (with deduplication)
        if fetched_items:
            # Read existing inbox to filter duplicates
            existing_inbox = self.storage.read_inbox()
            existing_ids = {(item.get("source"), item.get("original_id"), item.get("author_id")) for item in existing_inbox}

            # Filter out duplicates (use source+original_id+author_id to allow retweets from different accounts)
            new_items = [
                item for item in fetched_items
                if (item.get("source"), item.get("original_id"), item.get("author_id")) not in existing_ids
            ]

            if new_items:
                self.storage.write_inbox(new_items)
                self.logger.info(f"Wrote {len(new_items)} new items to inbox (filtered {len(fetched_items) - len(new_items)} duplicates)")
            else:
                self.logger.info("No new items to write (all duplicates)")
                fetched_items = new_items  # Update for return value

            # Index in vector store (if enabled)
            if self.settings.use_lancedb:
                try:
                    self.vector_store.index_items(fetched_items)
                    self.logger.info("Indexed items in LanceDB")
                except Exception as e:
                    self.logger.warning(f"LanceDB indexing failed: {e}")
            else:
                self.logger.debug("LanceDB disabled, skipping indexing")

        return WorkflowResult(
            success=True,
            items_processed=len(fetched_items),
            errors=errors,
            metadata={
                "x_creators_processed": len(x_creators),
                "rss_feeds_processed": len(rss_feeds),
            },
        )

    def _run_curation(self) -> WorkflowResult:
        """
        Stage 2: LLM evaluation and filtering.

        Returns:
            WorkflowResult with curation details
        """
        self.logger.info("Stage 2: Curation - Evaluating content")

        # Read inbox items
        inbox_items = self.storage.read_inbox()

        if not inbox_items:
            self.logger.warning("No items in inbox to curate")
            return WorkflowResult(
                success=True,
                items_processed=0,
                metadata={"message": "No items to curate"},
            )

        # Limit items to evaluate (for cost control)
        items_to_evaluate = inbox_items
        if len(inbox_items) > self.settings.max_curate_items:
            self.logger.info(f"Limiting evaluation to {self.settings.max_curate_items} items (from {len(inbox_items)} total)")
            items_to_evaluate = inbox_items[:self.settings.max_curate_items]

        self.logger.info(f"Evaluating {len(items_to_evaluate)} inbox items")

        # Evaluate with LLM
        curated_items = self.curator.evaluate_items(inbox_items)

        if not curated_items:
            self.logger.warning("No items were successfully curated")
            return WorkflowResult(
                success=True,
                items_processed=0,
                metadata={"message": "Curation produced no results"},
            )

        # Filter and rank
        top_items = self.ranker.filter_and_rank(
            curated_items,
            min_score=self.settings.curation_min_score,
            top_k=self.settings.curation_top_k,
        )

        # Get statistics
        stats = self.ranker.get_statistics(curated_items)
        self.logger.info(f"Curation stats: {stats}")

        if not top_items:
            self.logger.warning("No items met the score threshold")
            return WorkflowResult(
                success=True,
                items_processed=0,
                metadata={"message": "No items met score threshold", "stats": stats},
            )

        # Write to curated
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        curated_data = [item.model_dump() for item in top_items]
        self.storage.write_curated(date_str, curated_data)

        self.logger.info(f"Wrote {len(top_items)} curated items to curated/{date_str}_ranked.jsonl")

        # Remove only the evaluated items from inbox
        removed_count = self.storage.remove_inbox_items(items_to_evaluate)
        remaining_count = len(inbox_items) - removed_count
        self.logger.info(f"Removed {removed_count} evaluated items from inbox ({remaining_count} items remaining)")

        return WorkflowResult(
            success=True,
            items_processed=len(top_items),
            metadata={
                "date": date_str,
                "stats": stats,
                "curated_file": f"curated/{date_str}_ranked.jsonl",
            },
        )

    def _run_generation(self) -> WorkflowResult:
        """
        Stage 3: Blog post generation.

        Returns:
            WorkflowResult with generation details
        """
        self.logger.info("Stage 3: Generation - Creating blog posts")

        if not self.settings.blog_generation_enabled:
            self.logger.info("Blog generation is disabled")
            return WorkflowResult(
                success=True,
                items_processed=0,
                metadata={"message": "Blog generation disabled"},
            )

        # Read today's curated items
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        curated_items_data = self.storage.read_curated(date_str)

        if not curated_items_data:
            self.logger.warning(f"No curated items found for {date_str}")
            return WorkflowResult(
                success=True,
                items_processed=0,
                metadata={"message": "No curated items to generate from"},
            )

        self.logger.info(f"Found {len(curated_items_data)} curated items")

        # Convert to CuratedItem objects
        from growth_agent.core.schema import CuratedItem

        curated_items = [CuratedItem(**item) for item in curated_items_data]

        # Generate blog
        try:
            blog_post = self.blog_generator.generate_blog(
                curated_items=curated_items,
                context="AI and technology insights for business growth",
            )

            # Save blog
            filename = f"{blog_post.id}_{blog_post.slug}.md"
            self.storage.write_blog(filename, blog_post)

            self.logger.info(f"Saved blog post: blogs/{filename}")
            self.logger.info(f"  Title: {blog_post.frontmatter.title}")

            # Archive curated file
            self.storage.archive_curated(date_str)
            self.logger.info(f"Archived curated file to curated/archives/{date_str}_ranked.jsonl")

            return WorkflowResult(
                success=True,
                items_processed=1,
                metadata={
                    "blog_file": f"blogs/{filename}",
                    "blog_title": blog_post.frontmatter.title,
                    "blog_slug": blog_post.slug,
                    "source_items_count": len(blog_post.source_items),
                },
            )

        except Exception as e:
            self.logger.error(f"Blog generation failed: {e}")
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=[str(e)],
            )

    def cleanup(self) -> None:
        """Cleanup resources after execution."""
        # Close ingestors
        self.x_ingestor.close()
        self.rss_ingestor.close()
        self.logger.info("Cleanup complete")
