#!/usr/bin/env bash
# Workflow A: GitHub Issues Sync
# Sync GitHub issues to local storage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
uv run python scripts/sync_github_issues.py "$@"
