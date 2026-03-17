"""
Workflow C: Social Media Metrics Tracking.

Tracks engagement metrics for X/Twitter and LinkedIn posts.
"""

import logging
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Literal

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

        # Optional: Initialize new ingestors if configured
        self.gsc_ingestor = None
        self.posthog_ingestor = None

        try:
            if settings.gsc_enabled:
                from growth_agent.ingestors.gsc_search_console import GoogleSearchConsoleIngestor
                self.gsc_ingestor = GoogleSearchConsoleIngestor(settings)
                self.logger.info("GSC ingestor initialized")
        except Exception as e:
            self.logger.debug(f"GSC ingestor not available: {e}")

        try:
            if settings.posthog_enabled:
                from growth_agent.ingestors.posthog import PostHogIngestor
                self.posthog_ingestor = PostHogIngestor(settings)
                self.logger.info("PostHog ingestor initialized")
        except Exception as e:
            self.logger.debug(f"PostHog ingestor not available: {e}")

    def validate_prerequisites(self) -> bool:
        """
        Validate prerequisites for Workflow C.

        Checks:
        - X API credentials are configured (original requirement)
        - GSC configuration (optional)
        - PostHog configuration (optional)

        Returns:
            True if prerequisites are met
        """
        self.logger.info("Validating Workflow C prerequisites...")

        # Check X API credentials (original)
        if not self.settings.x_rapidapi_key:
            self.logger.error("X API key not configured (X_RAPIDAPI_KEY)")
            return False
        self.logger.info("✓ X API configured")

        # Check GSC configuration (optional)
        if self.gsc_ingestor:
            if not self.settings.gsc_site_url:
                self.logger.warning("GSC enabled but site URL not configured")
            else:
                self.logger.info("✓ GSC configured")

        # Check PostHog configuration (optional)
        if self.posthog_ingestor:
            if not self.settings.posthog_api_key:
                self.logger.warning("PostHog enabled but API key not configured")
            else:
                self.logger.info("✓ PostHog configured")

        return True

    def execute(
        self,
        data_source: Literal["x", "gsc", "posthog", "all"] = "all",
        username: str | None = None,
        user_id: str | None = None,
        count: int = 20,
        site_url: str | None = None,
        days: int = 7,
    ) -> WorkflowResult:
        """
        Execute metrics tracking workflow for specified data source.

        Args:
            data_source: Which data source to fetch ("x", "gsc", "posthog", "all")
            username: X username to track (without @)
            user_id: X user ID (numeric string)
            count: Number of recent tweets to track
            site_url: Site URL for GSC
            days: Number of days for GSC/PostHog lookback

        Returns:
            WorkflowResult with tracking details
        """
        self.logger.info(f"Starting Workflow C: {data_source} metrics tracking")

        errors = []
        metadata = {
            "data_source": data_source,
            "recorded_at": datetime.now(UTC).isoformat(),
        }

        try:
            # Route to appropriate executor based on data_source
            if data_source in ["x", "all"]:
                if username:
                    x_result = self.execute_x_metrics(username, user_id, count)
                    metadata["x_metrics"] = x_result.metadata
                    errors.extend(x_result.errors)

            if data_source in ["gsc", "all"]:
                if self.gsc_ingestor and site_url:
                    gsc_result = self.execute_gsc_metrics(site_url, days)
                    metadata["gsc_metrics"] = gsc_result.metadata
                    errors.extend(gsc_result.errors)

            if data_source in ["posthog", "all"]:
                if self.posthog_ingestor:
                    ph_result = self.execute_posthog_metrics(days)
                    metadata["posthog_metrics"] = ph_result.metadata
                    errors.extend(ph_result.errors)

            return WorkflowResult(
                success=len(errors) == 0,
                items_processed=metadata.get("fetched_count", 0),
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

    def execute_x_metrics(
        self,
        username: str,
        user_id: str | None = None,
        count: int = 20,
    ) -> WorkflowResult:
        """
        Execute X/Twitter metrics tracking (original Workflow C logic).

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

        self.logger.info(f"Starting X metrics tracking for @{username}")

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

            # Step 3: Load existing metrics for comparison
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

            # Step 4: Calculate deltas
            self.logger.info("Calculating totals...")
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

            # Step 5: Save metrics to storage
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
            self.logger.info("✓ X metrics tracking completed successfully")
            return WorkflowResult(
                success=True,
                items_processed=len(metrics_list),
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Unexpected error in X metrics tracking: {e}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=errors,
                metadata=metadata,
            )

    def execute_gsc_metrics(
        self,
        site_url: str,
        days: int = 7,
    ) -> WorkflowResult:
        """
        Execute Google Search Console metrics tracking.

        Args:
            site_url: Site URL for GSC (e.g., https://example.com)
            days: Number of days to look back

        Returns:
            WorkflowResult with tracking details
        """
        self.logger.info(f"Starting GSC metrics tracking for {site_url}")

        errors = []
        metadata = {
            "site_url": site_url,
            "days": days,
            "recorded_at": datetime.now(UTC).isoformat(),
        }

        all_metrics = []

        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Fetch search analytics data
            self.logger.info("Fetching GSC search analytics...")
            try:
                search_analytics = self.gsc_ingestor.fetch_search_analytics(
                    site_url=site_url,
                    start_date=start_date,
                    end_date=end_date,
                    dimensions=["page", "query"],
                    row_limit=100,
                )
                all_metrics.extend(search_analytics)
                metadata["search_analytics_count"] = len(search_analytics)
                self.logger.info(f"Fetched {len(search_analytics)} search analytics records")
            except Exception as e:
                error_msg = f"Failed to fetch search analytics: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch Core Web Vitals data
            self.logger.info("Fetching GSC Core Web Vitals (mobile)...")
            try:
                cwv_mobile = self.gsc_ingestor.fetch_core_web_vitals(
                    site_url=site_url,
                    mobile=True,
                )
                all_metrics.extend(cwv_mobile)
                self.logger.info(f"Fetched {len(cwv_mobile)} CWV mobile records")
            except Exception as e:
                error_msg = f"Failed to fetch CWV mobile: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch Core Web Vitals data (desktop)
            self.logger.info("Fetching GSC Core Web Vitals (desktop)...")
            try:
                cwv_desktop = self.gsc_ingestor.fetch_core_web_vitals(
                    site_url=site_url,
                    mobile=False,
                )
                all_metrics.extend(cwv_desktop)
                self.logger.info(f"Fetched {len(cwv_desktop)} CWV desktop records")
            except Exception as e:
                error_msg = f"Failed to fetch CWV desktop: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Save all metrics to storage
            if all_metrics:
                self.logger.info("Saving GSC metrics to storage...")
                try:
                    metrics_data = [metric.model_dump(mode="json") for metric in all_metrics]
                    self.storage.write_gsc_metrics(metrics_data)
                    metadata["total_count"] = len(all_metrics)
                    self.logger.info(f"Saved {len(metrics_data)} GSC metrics to metrics/gsc_stats.jsonl")
                except Exception as e:
                    error_msg = f"Failed to save GSC metrics: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            else:
                self.logger.warning("No GSC metrics fetched")

            # Success (even if some parts failed)
            success = len(errors) == 0 or len(all_metrics) > 0
            return WorkflowResult(
                success=success,
                items_processed=len(all_metrics),
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Unexpected error in GSC metrics tracking: {e}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=errors,
                metadata=metadata,
            )

    def execute_posthog_metrics(
        self,
        days: int = 1,
    ) -> WorkflowResult:
        """
        Execute PostHog metrics tracking.

        Args:
            days: Number of days to look back

        Returns:
            WorkflowResult with tracking details
        """
        self.logger.info(f"Starting PostHog metrics tracking (last {days} days)")

        errors = []
        metadata = {
            "days": days,
            "recorded_at": datetime.now(UTC).isoformat(),
        }

        all_metrics = []

        try:
            # Fetch feature flags
            self.logger.info("Fetching PostHog feature flags...")
            try:
                flags = self.posthog_ingestor.fetch_feature_flags(active_only=True)
                all_metrics.extend(flags)
                metadata["flags_count"] = len(flags)
                self.logger.info(f"Fetched {len(flags)} feature flags")
            except Exception as e:
                error_msg = f"Failed to fetch feature flags: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch events
            self.logger.info("Fetching PostHog events...")
            try:
                events = self.posthog_ingestor.fetch_events(limit=100)
                all_metrics.extend(events)
                metadata["events_count"] = len(events)
                self.logger.info(f"Fetched {len(events)} events")
            except Exception as e:
                error_msg = f"Failed to fetch events: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch insights
            self.logger.info("Fetching PostHog insights...")
            try:
                insights = self.posthog_ingestor.fetch_insights(days=days)
                all_metrics.extend(insights)
                metadata["insights_count"] = len(insights)
                self.logger.info(f"Fetched {len(insights)} insights")
            except Exception as e:
                error_msg = f"Failed to fetch insights: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch funnels
            self.logger.info("Fetching PostHog funnels...")
            try:
                funnels = self.posthog_ingestor.fetch_funnels(days=days)
                all_metrics.extend(funnels)
                metadata["funnels_count"] = len(funnels)
                self.logger.info(f"Fetched {len(funnels)} funnel steps")
            except Exception as e:
                error_msg = f"Failed to fetch funnels: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch event properties
            self.logger.info("Fetching PostHog event properties...")
            try:
                event_properties = self.posthog_ingestor.fetch_event_properties()
                all_metrics.extend(event_properties)
                metadata["event_properties_count"] = len(event_properties)
                self.logger.info(f"Fetched {len(event_properties)} event properties")
            except Exception as e:
                error_msg = f"Failed to fetch event properties: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Fetch person properties
            self.logger.info("Fetching PostHog person properties...")
            try:
                person_properties = self.posthog_ingestor.fetch_person_properties()
                all_metrics.extend(person_properties)
                metadata["person_properties_count"] = len(person_properties)
                self.logger.info(f"Fetched {len(person_properties)} person properties")
            except Exception as e:
                error_msg = f"Failed to fetch person properties: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

            # Save all metrics to storage
            if all_metrics:
                self.logger.info("Saving PostHog metrics to storage...")
                try:
                    metrics_data = [metric.model_dump(mode="json") for metric in all_metrics]
                    self.storage.write_posthog_metrics(metrics_data)
                    metadata["total_count"] = len(all_metrics)
                    self.logger.info(f"Saved {len(metrics_data)} PostHog metrics to metrics/posthog_stats.jsonl")
                except Exception as e:
                    error_msg = f"Failed to save PostHog metrics: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
            else:
                self.logger.warning("No PostHog metrics fetched")

            # Success (even if some parts failed)
            success = len(errors) == 0 or len(all_metrics) > 0
            return WorkflowResult(
                success=success,
                items_processed=len(all_metrics),
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Unexpected error in PostHog metrics tracking: {e}"
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
