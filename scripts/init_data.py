#!/usr/bin/env python
"""
Initialize data directory with empty files.

This script creates the directory structure and empty data files.
"""

import json
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4


def init_data_dir(data_root: Path = Path("data")) -> None:
    """Initialize data directory structure."""
    print(f"Initializing data directory: {data_root.resolve()}")

    # Create directories
    directories = [
        "subscriptions",
        "inbox",
        "curated/archives",
        "blogs",
        "github",
        "metrics",
        "logs",
        "index",
        "schemas",
    ]

    for dir_path in directories:
        full_path = data_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {dir_path}/")

    # Create empty subscription files
    x_creators = data_root / "subscriptions" / "x_creators.jsonl"
    rss_feeds = data_root / "subscriptions" / "rss_feeds.jsonl"

    if not x_creators.exists():
        x_creators.touch()
        print(f"  ✓ Created subscriptions/x_creators.jsonl")

    if not rss_feeds.exists():
        rss_feeds.touch()
        print(f"  ✓ Created subscriptions/rss_feeds.jsonl")

    # Create manifest.json if it doesn't exist
    manifest = data_root / "manifest.json"
    if not manifest.exists():
        manifest_data = {
            "version": "1.0.0",
            "last_updated": datetime.now(UTC).isoformat(),
            "data_root": str(data_root),
        }
        manifest.write_text(json.dumps(manifest_data, indent=2) + "\n")
        print(f"  ✓ Created manifest.json")

    print("\n✓ Initialization complete!")
    print(f"\nData root: {data_root.resolve()}")
    print("\nNext steps:")
    print("  1. Copy .env.example to .env and add your API keys")
    print("  2. Add subscriptions:")
    print("     - Edit subscriptions/x_creators.jsonl")
    print("     - Edit subscriptions/rss_feeds.jsonl")
    print("  3. Run: python -m growth_agent.main init")
    print("  4. Run: python -m growth_agent.main run workflow-b")


if __name__ == "__main__":
    init_data_dir()
