#!/usr/bin/env bash
# Workflow B: Content Intelligence & Blog Generation
# Ingest, curate, and generate blog posts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
uv run python -m growth_agent.main run workflow-b "$@"
