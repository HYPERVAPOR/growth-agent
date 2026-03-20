#!/usr/bin/env bash
# Workflow D: PuppyOne Social Listener
# Discover social opportunities and blog ideas, optionally render images and post to Discord

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
uv run python -m growth_agent.main run workflow-d "$@"
