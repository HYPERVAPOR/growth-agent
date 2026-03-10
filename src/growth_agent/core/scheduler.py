"""
APScheduler integration for workflow execution.

This module provides cron-based scheduling for automated workflow execution.
"""

import logging
import signal
import sys
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from growth_agent.config import Settings
from growth_agent.workflows.base import Workflow

logger = logging.getLogger(__name__)


def setup_scheduler(settings: Settings, workflows: dict[str, Workflow]) -> AsyncIOScheduler:
    """
    Setup APScheduler for automated workflow execution.

    Args:
        settings: Application settings
        workflows: Dictionary of workflow name to workflow instance

    Returns:
        Configured AsyncIOScheduler instance
    """
    # Create scheduler with timezone
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    # Schedule Workflow B for daily execution at 8 AM Beijing time
    if "workflow_b" in workflows:
        schedule = settings.ingestion_schedule  # "0 8 * * *" format (minute hour day month weekday)
        parts = schedule.split()
        minute, hour = parts[0], parts[1]  # Extract minute and hour

        scheduler.add_job(
            workflows["workflow_b"].run,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id="workflow_b_daily",
            name="Workflow B - Daily Content Intelligence",
            replace_existing=True,
        )

        logger.info(f"Scheduled Workflow B for daily execution at {hour}:{minute} {settings.scheduler_timezone}")

    # Schedule Workflow C: GSC metrics (daily at 9 AM)
    if "workflow_c" in workflows and settings.gsc_enabled:
        gsc_schedule = settings.gsc_schedule
        parts = gsc_schedule.split()
        minute, hour = parts[0], parts[1]

        scheduler.add_job(
            lambda: workflows["workflow_c"].execute(
                data_source="gsc",
                site_url=settings.gsc_site_url,
                days=7,
            ),
            CronTrigger(hour=int(hour), minute=int(minute)),
            id="workflow_c_gsc_daily",
            name="Workflow C - GSC Daily Metrics",
            replace_existing=True,
        )

        logger.info(f"Scheduled GSC metrics for daily at {hour}:{minute}")

    # Schedule Workflow C: PostHog metrics (every 6 hours)
    if "workflow_c" in workflows and settings.posthog_enabled:
        ph_schedule = settings.posthog_schedule
        parts = ph_schedule.split()

        scheduler.add_job(
            lambda: workflows["workflow_c"].execute(
                data_source="posthog",
                days=1,
            ),
            CronTrigger(
                minute=int(parts[0]),
                hour=int(parts[1]) if len(parts) > 1 else None,
            ),
            id="workflow_c_posthog_6h",
            name="Workflow C - PostHog Every 6 Hours",
            replace_existing=True,
        )

        logger.info("Scheduled PostHog metrics for every 6 hours")

    if "workflow_d" in workflows and settings.social_listener_enabled:
        social_schedule = settings.social_listener_schedule
        parts = social_schedule.split()
        minute, hour = parts[0], parts[1]

        scheduler.add_job(
            workflows["workflow_d"].run,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id="workflow_d_daily",
            name="Workflow D - PuppyOne Social Listener",
            replace_existing=True,
        )

        logger.info("Scheduled Workflow D for daily execution at %s:%s", hour, minute)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    return scheduler


def run_scheduler(settings: Settings, workflows: dict[str, Workflow]) -> None:
    """
    Run the scheduler daemon.

    Args:
        settings: Application settings
        workflows: Dictionary of workflow name to workflow instance
    """
    import asyncio

    logger.info("Starting scheduler daemon")

    async def run_async() -> None:
        """Run scheduler in async context."""
        scheduler = setup_scheduler(settings, workflows)

        # Start scheduler
        scheduler.start()

        logger.info("Scheduler started, waiting for next scheduled execution...")
        logger.info("Press Ctrl+C to stop")

        # Keep the program running
        try:
            # Sleep forever, checking every hour
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
            scheduler.shutdown()

    # Run the async scheduler
    try:
        asyncio.run(run_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
