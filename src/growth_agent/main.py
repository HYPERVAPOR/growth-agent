"""
CLI entry point for Growth Agent.

This module provides command-line interface for running workflows and managing the system.
"""

import sys
from pathlib import Path

import click

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.scheduler import run_scheduler
from growth_agent.core.storage import StorageManager
from growth_agent.workflows.workflow_a import WorkflowA
from growth_agent.workflows.workflow_b import WorkflowB
from growth_agent.workflows.workflow_c import WorkflowC


def init_workflows(settings: Settings, storage: StorageManager) -> dict:
    """
    Initialize all workflow instances.

    Args:
        settings: Application settings
        storage: Storage manager instance

    Returns:
        Dictionary of workflow name to workflow instance
    """
    return {
        "workflow_a": WorkflowA(settings, storage),
        "workflow_b": WorkflowB(settings, storage),
        "workflow_c": WorkflowC(settings, storage),
    }


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cli(verbose: bool) -> None:
    """
    Growth Agent - AI-driven growth and operations system.

    Commands:
        init        Initialize data directory
        run         Run a workflow
        schedule    Start scheduler daemon
    """
    # Load settings
    settings = reload_settings()

    # Adjust log level if verbose
    if verbose:
        settings.log_level = "DEBUG"

    # Setup logging
    setup_logging(settings)

    # Store settings in context for subcommands
    click.ctx.obj = {"settings": settings}


@cli.command()
def init() -> None:
    """Initialize data directory and create empty data files."""
    settings = reload_settings()
    setup_logging(settings)

    click.echo(f"Initializing data directory: {settings.data_root}")

    # Create storage manager (this will create directories)
    storage = StorageManager(settings.data_root)

    click.echo("✓ Directory structure created")
    click.echo(f"  Data root: {settings.data_root}")

    # Create empty subscription files if they don't exist
    x_creators_path = settings.data_root / "subscriptions" / "x_creators.jsonl"
    rss_feeds_path = settings.data_root / "subscriptions" / "rss_feeds.jsonl"

    if not x_creators_path.exists():
        x_creators_path.touch()
        click.echo("✓ Created subscriptions/x_creators.jsonl")

    if not rss_feeds_path.exists():
        rss_feeds_path.touch()
        click.echo("✓ Created subscriptions/rss_feeds.jsonl")

    click.echo("\nInitialization complete!")
    click.echo("\nNext steps:")
    click.echo("1. Add X creators to subscriptions/x_creators.jsonl")
    click.echo("2. Add RSS feeds to subscriptions/rss_feeds.jsonl")
    click.echo("3. Run: growth-agent run workflow-b")


@cli.command()
@click.argument("workflow", type=click.Choice(["workflow-a", "workflow-b", "workflow-c"]))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def run(workflow: str, verbose: bool) -> None:
    """Run a workflow manually."""
    # Load settings and setup logging
    settings = reload_settings()
    if verbose:
        settings.log_level = "DEBUG"
    setup_logging(settings)

    # Initialize storage
    storage = StorageManager(settings.data_root)

    # Initialize workflows
    workflows = init_workflows(settings, storage)

    # Map workflow name to instance
    workflow_map = {
        "workflow-a": "workflow_a",
        "workflow-b": "workflow_b",
        "workflow-c": "workflow_c",
    }

    workflow_key = workflow_map.get(workflow)
    if not workflow_key or workflow_key not in workflows:
        click.echo(f"Error: Unknown workflow '{workflow}'", err=True)
        sys.exit(1)

    workflow_instance = workflows[workflow_key]

    click.echo(f"Running {workflow}...")

    # Run workflow
    result = workflow_instance.run()

    # Display results
    if result.success:
        click.echo(f"✓ {workflow} completed successfully")
        click.echo(f"  Items processed: {result.items_processed}")

        if result.metadata:
            click.echo("\nMetadata:")
            for key, value in result.metadata.items():
                if isinstance(value, dict):
                    click.echo(f"  {key}:")
                    for k, v in value.items():
                        click.echo(f"    {k}: {v}")
                else:
                    click.echo(f"  {key}: {value}")
    else:
        click.echo(f"✗ {workflow} failed", err=True)
        if result.errors:
            click.echo("\nErrors:")
            for error in result.errors:
                click.echo(f"  - {error}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def schedule(verbose: bool) -> None:
    """Start scheduler daemon for automated workflow execution."""
    # Load settings and setup logging
    settings = reload_settings()
    if verbose:
        settings.log_level = "DEBUG"
    setup_logging(settings)

    # Initialize storage
    storage = StorageManager(settings.data_root)

    # Initialize workflows
    workflows = init_workflows(settings, storage)

    click.echo(f"Starting scheduler daemon (timezone: {settings.scheduler_timezone})")
    click.echo(f"Workflow B scheduled for: {settings.ingestion_schedule}")
    click.echo("Press Ctrl+C to stop\n")

    # Run scheduler (this will block)
    try:
        run_scheduler(settings, workflows)
    except KeyboardInterrupt:
        click.echo("\nScheduler stopped")


def main() -> None:
    """Main entry point."""
    cli(obj={}, standalone_mode=False)


if __name__ == "__main__":
    main()
