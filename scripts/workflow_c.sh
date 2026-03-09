#!/usr/bin/env bash
# Workflow C: Multi-Platform Analytics Tracking
# Sync metrics from X/Twitter, Google Search Console, and PostHog

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Default values
SOURCE="all"
DAYS=7

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        *)
            # Pass other arguments to the Python script
            break
            ;;
    esac
done

uv run python scripts/sync_metrics.py --source "$SOURCE" --days "$DAYS" "$@"
