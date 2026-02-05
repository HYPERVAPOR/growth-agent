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
        schedule = settings.ingestion_schedule  # "0 8 * * *" format
        hour, minute = schedule.split()[1:3]  # Extract hour and minute

        scheduler.add_job(
            workflows["workflow_b"].run,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id="workflow_b_daily",
            name="Workflow B - Daily Content Intelligence",
            replace_existing=True,
        )

        logger.info(f"Scheduled Workflow B for daily execution at {hour}:{minute} {settings.scheduler_timezone}")

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
    logger.info("Starting scheduler daemon")

    scheduler = setup_scheduler(settings, workflows)

    # Start scheduler
    scheduler.start()

    logger.info("Scheduler started, waiting for next scheduled execution...")
    logger.info("Press Ctrl+C to stop")

    # Keep the program running
    try:
        import asyncio

        # Create a never-ending coroutine
        async def run_forever() -> None:
            while True:
                await asyncio.sleep(3600)  # Sleep 1 hour at a time

        asyncio.run(run_forever())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
        scheduler.shutdown()
