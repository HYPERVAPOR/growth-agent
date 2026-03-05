#!/usr/bin/env python3
"""
Test script for inbox selection strategies.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from growth_agent.config import SelectionStrategy, Settings, get_settings


def load_inbox():
    """Load inbox items."""
    inbox_path = Path("data/inbox/items.jsonl")
    if not inbox_path.exists():
        print(f"❌ Inbox file not found: {inbox_path}")
        return []

    items = []
    with open(inbox_path) as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    return items


def select_items(items, strategy, settings):
    """Select items using the given strategy."""
    max_items = settings.max_curate_items

    if len(items) <= max_items:
        return items

    if strategy == SelectionStrategy.RECENT_FIRST:
        sorted_items = sorted(
            items,
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        return sorted_items[:max_items]

    elif strategy == SelectionStrategy.RANDOM:
        import random
        return random.sample(items, max_items)

    elif strategy == SelectionStrategy.BALANCED:
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in items:
            if item.get('source') == 'x':
                key = ('x', item.get('author_name', 'unknown'))
            elif item.get('source') == 'rss':
                key = ('rss', item.get('feed_title', 'unknown'))
            else:
                key = (item.get('source', 'unknown'), 'unknown')
            grouped[key].append(item)

        sampled = []
        max_per_source = settings.max_items_per_source_selection

        for group_items in grouped.values():
            sorted_group = sorted(
                group_items,
                key=lambda x: x.get('published_at', ''),
                reverse=True
            )
            sampled.extend(sorted_group[:max_per_source])

        sampled_sorted = sorted(
            sampled,
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        return sampled_sorted[:max_items]

    else:  # CHRONOLOGICAL
        return items[:max_items]


def analyze_selection(selected_items, strategy_name):
    """Analyze selected items."""
    print(f"\n{'='*60}")
    print(f"Strategy: {strategy_name}")
    print(f"{'='*60}")

    # Count by source
    sources = Counter(item.get('source') for item in selected_items)
    print(f"\n📊 Source distribution:")
    for source, count in sources.most_common():
        print(f"  {source}: {count}")

    # Count by author (for X) or feed (for RSS)
    if sources.get('x'):
        authors = Counter(item.get('author_name') for item in selected_items if item.get('source') == 'x')
        print(f"\n🐦 Top X creators:")
        for author, count in authors.most_common(10):
            print(f"  @{author}: {count}")

    if sources.get('rss'):
        feeds = Counter(item.get('feed_title') for item in selected_items if item.get('source') == 'rss')
        print(f"\n📰 Top RSS feeds:")
        for feed, count in feeds.most_common(10):
            print(f"  {feed}: {count}")

    # Time range
    published_times = [item.get('published_at') for item in selected_items if item.get('published_at')]
    if published_times:
        times = sorted(published_times)
        print(f"\n⏰ Time range:")
        print(f"  Oldest: {times[0]}")
        print(f"  Newest: {times[-1]}")

    # Sample items
    print(f"\n📝 Sample items (top 3):")
    for i, item in enumerate(selected_items[:3], 1):
        source = item.get('source', 'unknown')
        if source == 'x':
            author = item.get('author_name', 'unknown')
            content = item.get('content', '')[:80]
            print(f"  {i}. [@{author}] {content}...")
        elif source == 'rss':
            feed = item.get('feed_title', 'unknown')
            title = item.get('title', '')[:60]
            print(f"  {i}. [{feed}] {title}...")


def main():
    print("🧪 Testing Inbox Selection Strategies")
    print("="*60)

    # Load data
    items = load_inbox()
    if not items:
        print("❌ No items to test")
        return

    print(f"\n📦 Total items in inbox: {len(items)}")

    # Get settings
    settings = get_settings()
    print(f"⚙️  MAX_CURATE_ITEMS: {settings.max_curate_items}")
    print(f"⚙️  MAX_ITEMS_PER_SOURCE_SELECTION: {settings.max_items_per_source_selection}")

    # Test each strategy
    strategies = [
        SelectionStrategy.RECENT_FIRST,
        SelectionStrategy.RANDOM,
        SelectionStrategy.BALANCED,
        SelectionStrategy.CHRONOLOGICAL,
    ]

    for strategy in strategies:
        selected = select_items(items, strategy, settings)
        analyze_selection(selected, strategy.value)

    print(f"\n{'='*60}")
    print("✅ Test complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
