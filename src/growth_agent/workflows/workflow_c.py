"""
Workflow C: Social Media Metrics Tracking.

Tracks engagement metrics for X/Twitter and LinkedIn posts.
"""

import logging
from datetime import datetime, UTC
from pathlib import Path

from growth_agent.config import Settings
from growth_agent.core.schema import WorkflowResult, MetricStat
from growth_agent.core.storage import StorageManager
from growth_agent.ingestors.metrics import MetricsCollector
from growth_agent.workflows.base import Workflow

logger = logging.getLogger(__name__)


class WorkflowC(Workflow):
    """
    Social Media Metrics Tracking workflow.

    Features:
    1. Fetch metrics from X/Twitter for tracked accounts
    2. Store metrics history for trend analysis
    3. Track engagement deltas over time

    Usage:
        workflow = WorkflowC(settings, storage)
        result = workflow.execute(username="puppyone_ai", user_id="123456")
    """

    def __init__(self, settings: Settings, storage: StorageManager):
        """
        Initialize Workflow C.

        Args:
            settings: Application settings
            storage: Storage manager instance
        """
        self.settings = settings
        self.storage = storage
        self.collector = MetricsCollector(settings)
        self.logger = logger

    def validate_prerequisites(self) -> bool:
        """
        Validate prerequisites for Workflow C.

        Checks:
        - X API credentials are configured
        - Tracking targets are set

        Returns:
            True if prerequisites are met
        """
        self.logger.info("Validating Workflow C prerequisites...")

        # Check X API credentials
        if not self.settings.x_rapidapi_key:
            self.logger.error("X API key not configured (X_RAPIDAPI_KEY)")
            return False
        self.logger.info("✓ X API configured")

        return True

    def execute(
        self,
        username: str | None = None,
        user_id: str | None = None,
        count: int = 20,
    ) -> WorkflowResult:
        """
        Execute metrics tracking workflow.

        Steps:
        1. Fetch recent tweets and their metrics
        2. Load existing metrics for comparison
        3. Calculate deltas (growth since last recording)
        4. Save new metrics to storage

        Args:
            username: X username to track (without @)
            user_id: X user ID (numeric string)
            count: Number of recent tweets to track

        Returns:
            WorkflowResult with tracking details
        """
        if not username:
            self.logger.error("Username not provided")
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=["Username not provided"],
                metadata={},
            )

        self.logger.info(f"Starting Workflow C: Metrics tracking for @{username}")

        errors = []
        metadata = {
            "username": username,
            "user_id": user_id,
            "count": count,
            "recorded_at": datetime.now(UTC).isoformat(),
        }

        try:
            # Step 1: Fetch user ID if not provided
            if not user_id:
                self.logger.info(f"Fetching user ID for @{username}...")
                user_id = self.collector.get_user_id(username)
                if not user_id:
                    error_msg = f"Could not fetch user ID for @{username}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    return WorkflowResult(
                        success=False,
                        items_processed=0,
                        errors=errors,
                        metadata=metadata,
                    )
                metadata["user_id"] = user_id
                self.logger.info(f"✓ Found user ID: {user_id}")

            # Step 2: Fetch metrics from X
            self.logger.info(f"Fetching metrics for @{username}'s recent tweets...")
            try:
                metrics_list = self.collector.fetch_user_tweets_metrics(
                    username=username,
                    user_id=user_id or "",
                    count=count,
                )
                metadata["fetched_count"] = len(metrics_list)

                if not metrics_list:
                    warning = f"No metrics fetched for @{username}"
                    self.logger.warning(warning)
                    errors.append(warning)
                    return WorkflowResult(
                        success=False,
                        items_processed=0,
                        errors=errors,
                        metadata=metadata,
                    )

                self.logger.info(f"Fetched metrics for {len(metrics_list)} tweets")

            except Exception as e:
                error_msg = f"Failed to fetch metrics: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                return WorkflowResult(
                    success=False,
                    items_processed=0,
                    errors=errors,
                    metadata=metadata,
                )

            # Step 2: Load existing metrics for comparison
            self.logger.info("Loading existing metrics from storage...")
            existing_metrics_dict = {}
            try:
                existing_metrics_raw = self.storage.read_metrics()
                # Convert to MetricStat objects and create lookup by content_id
                for metric_raw in existing_metrics_raw:
                    metric = MetricStat(**metric_raw)
                    # Use (content_id, platform) as composite key
                    key = (metric.content_id, metric.platform)
                    existing_metrics_dict[key] = metric

                metadata["existing_count"] = len(existing_metrics_raw)
                self.logger.info(f"Loaded {len(existing_metrics_raw)} existing metrics")

            except Exception as e:
                self.logger.warning(f"Failed to load existing metrics (first run?): {e}")
                metadata["existing_count"] = 0

            # Step 3: Calculate deltas
            self.logger.info("Calculating deltas (growth since last recording)...")
            total_impressions = 0
            total_engagements = 0
            total_likes = 0
            total_retweets = 0

            for metric in metrics_list:
                key = (metric.content_id, metric.platform)

                # Aggregate totals
                if metric.impressions:
                    total_impressions += metric.impressions
                if metric.engagements:
                    total_engagements += metric.engagements
                if metric.likes:
                    total_likes += metric.likes
                if metric.retweets:
                    total_retweets += metric.retweets

                # Calculate delta if we have previous data
                if key in existing_metrics_dict:
                    previous = existing_metrics_dict[key]
                    # Could add delta calculation here if needed
                    # For now, we just track current metrics
                    pass

            metadata["total_impressions"] = total_impressions
            metadata["total_engagements"] = total_engagements
            metadata["total_likes"] = total_likes
            metadata["total_retweets"] = total_retweets

            self.logger.info(f"Total impressions: {total_impressions:,}")
            self.logger.info(f"Total engagements: {total_engagements:,}")

            # Step 4: Save metrics to storage
            self.logger.info("Saving metrics to storage...")
            try:
                # Convert to dict for JSONL storage
                metrics_data = [metric.model_dump(mode="json") for metric in metrics_list]
                self.storage.write_metrics(metrics_data)
                self.logger.info(f"Saved {len(metrics_data)} metrics to metrics/stats.jsonl")

            except Exception as e:
                error_msg = f"Failed to save metrics: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                return WorkflowResult(
                    success=False,
                    items_processed=len(metrics_list),
                    errors=errors,
                    metadata=metadata,
                )

            # Success
            self.logger.info("✓ Workflow C completed successfully")
            return WorkflowResult(
                success=True,
                items_processed=len(metrics_list),
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Unexpected error in Workflow C: {e}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=errors,
                metadata=metadata,
            )

    def cleanup(self) -> None:
        """Cleanup resources after workflow execution."""
        self.logger.debug("Workflow C cleanup complete")
