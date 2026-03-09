#!/usr/bin/env python
"""
Manual trigger for social media and external metrics synchronization.

This script fetches engagement metrics from X/Twitter, Google Search Console,
and PostHog, then saves them for tracking.
"""
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.storage import StorageManager
from growth_agent.workflows.workflow_c import WorkflowC


def main():
    """Manually trigger metrics synchronization."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Sync metrics from various platforms (X/Twitter, GSC, PostHog)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync X/Twitter metrics
  python sync_metrics.py --source x --username puppyone_ai

  # Sync Google Search Console metrics
  python sync_metrics.py --source gsc --site-url https://example.com --days 7

  # Sync PostHog metrics
  python sync_metrics.py --source posthog --days 1

  # Sync all data sources
  python sync_metrics.py --source all
        """
    )

    parser.add_argument(
        "--source",
        choices=["x", "gsc", "posthog", "all"],
        default="x",
        help="Data source to sync (default: x)"
    )
    parser.add_argument(
        "--username",
        help="X username (without @) for X metrics"
    )
    parser.add_argument(
        "--user-id",
        help="X user ID for X metrics"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of tweets to fetch for X metrics (default: 20)"
    )
    parser.add_argument(
        "--site-url",
        help="Site URL for GSC metrics (e.g., https://example.com)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for GSC/PostHog metrics (default: 7)"
    )

    args = parser.parse_args()

    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("External Metrics Synchronization")
    print("=" * 60)

    # Initialize storage
    storage = StorageManager(settings.data_root)
    workflow = WorkflowC(settings, storage)

    # Validate prerequisites
    print("\nValidating prerequisites...")
    if not workflow.validate_prerequisites():
        print("\n✗ Prerequisites check failed")
        print("  Please ensure:")
        if args.source in ["x", "all"]:
            print("  1. X_RAPIDAPI_KEY is configured")
        if args.source in ["gsc", "all"] and settings.gsc_enabled:
            print("  2. GSC credentials are configured")
        if args.source in ["posthog", "all"] and settings.posthog_enabled:
            print("  3. PostHog credentials are configured")
        return 1

    print("✓ Prerequisites check passed")

    # Prepare execution parameters
    print(f"\nStarting synchronization for: {args.source}")
    if args.source == "x" or args.source == "all":
        if not args.username:
            # Default X account
            args.username = "puppyone_ai"
            args.user_id = "1689650211810123776"
        print(f"  X account: @{args.username}")
    if args.source in ["gsc", "all"] and settings.gsc_site_url:
        print(f"  GSC site: {args.site_url or settings.gsc_site_url}")
    if args.source in ["posthog", "all"] and settings.posthog_enabled:
        print(f"  PostHog: enabled")

    # Run sync
    result = workflow.execute(
        data_source=args.source,
        username=args.username,
        user_id=args.user_id,
        count=args.count,
        site_url=args.site_url or settings.gsc_site_url,
        days=args.days,
    )

    if result.success:
        print("\n" + "=" * 60)
        print("✓ Synchronization completed successfully!")
        print("=" * 60)

        metadata = result.metadata

        # Display X metrics if available
        if "x_metrics" in metadata:
            x_meta = metadata["x_metrics"]
            print(f"\nX/Twitter Metrics:")
            print(f"  Account: @{x_meta.get('username')}")
            print(f"  Tweets: {x_meta.get('fetched_count', 0)}")
            print(f"  Total impressions: {x_meta.get('total_impressions', 0):,}")
            print(f"  Total engagements: {x_meta.get('total_engagements', 0):,}")
            print(f"  Total likes: {x_meta.get('total_likes', 0):,}")
            print(f"  Total retweets: {x_meta.get('total_retweets', 0):,}")

        # Display GSC metrics if available
        if "gsc_metrics" in metadata:
            gsc_meta = metadata["gsc_metrics"]
            print(f"\nGoogle Search Console Metrics:")
            print(f"  Site: {gsc_meta.get('site_url')}")
            print(f"  Records: {gsc_meta.get('total_count', 0)}")
            print(f"  Search analytics: {gsc_meta.get('search_analytics_count', 0)}")

        # Display PostHog metrics if available
        if "posthog_metrics" in metadata:
            ph_meta = metadata["posthog_metrics"]
            print(f"\nPostHog Metrics:")
            print(f"  Total records: {ph_meta.get('total_count', 0)}")
            print(f"  Feature flags: {ph_meta.get('flags_count', 0)}")
            print(f"  Events: {ph_meta.get('events_count', 0)}")
            print(f"  Insights: {ph_meta.get('insights_count', 0)}")
            print(f"  Funnels: {ph_meta.get('funnels_count', 0)}")

        if result.errors:
            print(f"\n⚠ {len(result.errors)} warning(s):")
            for error in result.errors:
                print(f"  - {error}")

        # Display data file locations
        print("\nData saved to:")
        if args.source in ["x", "all"]:
            print("  - data/metrics/stats.jsonl (X/Twitter)")
        if args.source in ["gsc", "all"] and settings.gsc_enabled:
            print("  - data/metrics/gsc_stats.jsonl (GSC)")
        if args.source in ["posthog", "all"] and settings.posthog_enabled:
            print("  - data/metrics/posthog_stats.jsonl (PostHog)")

        return 0
    else:
        print("\n✗ Synchronization failed")
        if result.errors:
            print("\nError details:")
            for error in result.errors:
                print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
