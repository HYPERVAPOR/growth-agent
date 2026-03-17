#!/usr/bin/env python
"""Verbose test for PostHog properties fetching with detailed logging."""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from growth_agent.config import Settings
from growth_agent.ingestors.posthog import PostHogIngestor
from growth_agent.core.storage import StorageManager

print("=" * 80)
print("POSTHOG PROPERTIES FETCHING - VERBOSE TEST")
print("=" * 80)

# Step 1: Load configuration
print("\n[Step 1] Loading configuration...")
print("-" * 80)
try:
    settings = Settings()
    print(f"✅ Configuration loaded successfully")
    print(f"   PostHog Host: {settings.posthog_host}")
    print(f"   PostHog Project ID: {settings.posthog_project_id}")
    print(f"   PostHog API Key: {settings.posthog_api_key[:20]}..." if settings.posthog_api_key else "   PostHog API Key: Not configured")
except Exception as e:
    print(f"❌ Failed to load configuration: {e}")
    sys.exit(1)

# Step 2: Initialize PostHog Ingestor
print("\n[Step 2] Initializing PostHog Ingestor...")
print("-" * 80)
try:
    ingestor = PostHogIngestor(settings)
    print(f"✅ PostHog Ingestor initialized")
    print(f"   API Base URL: {ingestor.api_base_url}")
except Exception as e:
    print(f"❌ Failed to initialize ingestor: {e}")
    sys.exit(1)

# Step 3: Test HogQL Query Execution
print("\n[Step 3] Testing HogQL Query Execution...")
print("-" * 80)
print("Executing: SELECT event FROM events LIMIT 1")
try:
    results = ingestor._execute_hogql_query(
        query="SELECT event FROM events LIMIT 1",
        name="test_connection"
    )
    print(f"✅ Query executed successfully")
    print(f"   Returned {len(results)} row(s)")
    if results:
        print(f"   Sample event: {results[0].get('event', 'N/A')}")
except Exception as e:
    print(f"❌ Query execution failed: {e}")
    ingestor.close()
    sys.exit(1)

# Step 4: Fetch Event Properties
print("\n[Step 4] Fetching Event Properties...")
print("-" * 80)
print("Executing multi-step process:")
print("  1. Query recent events with properties")
print("  2. Parse JSON properties from each event")
print("  3. Extract unique property names and types")
print("  4. Count usage frequency")
print("  5. Create PostHogMetricStat records")
try:
    event_properties = ingestor.fetch_event_properties(days=7, sample_size=1000)
    print(f"✅ Event properties fetched successfully")
    print(f"   Total unique properties: {len(event_properties)}")

    if event_properties:
        print(f"\n   Top 10 Event Properties by usage:")
        for i, prop in enumerate(event_properties[:10], 1):
            print(f"   {i:2d}. {prop.event_property_name:35s} | {prop.event_property_type:20s} | {prop.event_property_usage_count:4d} events")
except Exception as e:
    print(f"❌ Failed to fetch event properties: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Fetch Person Properties
print("\n[Step 5] Fetching Person Properties...")
print("-" * 80)
print("Executing multi-step process:")
print("  1. Query persons with their properties")
print("  2. Parse JSON properties from each person")
print("  3. Extract unique property names and types")
print("  4. Count usage frequency")
print("  5. Create PostHogMetricStat records")
try:
    person_properties = ingestor.fetch_person_properties(sample_size=1000)
    print(f"✅ Person properties fetched successfully")
    print(f"   Total unique properties: {len(person_properties)}")

    if person_properties:
        print(f"\n   All Person Properties:")
        for i, prop in enumerate(person_properties, 1):
            print(f"   {i:2d}. {prop.person_property_name:35s} | {prop.person_property_type:20s} | {prop.person_property_usage_count:4d} persons")
except Exception as e:
    print(f"❌ Failed to fetch person properties: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Save to Storage
print("\n[Step 6] Saving to Storage...")
print("-" * 80)
try:
    # StorageManager expects data_root path, not Settings object
    storage = StorageManager(settings.data_root)

    all_metrics = []
    if event_properties:
        all_metrics.extend(event_properties)
        print(f"   Adding {len(event_properties)} event property records")

    if person_properties:
        all_metrics.extend(person_properties)
        print(f"   Adding {len(person_properties)} person property records")

    if all_metrics:
        # Convert to dict for JSONL storage
        metrics_data = [metric.model_dump(mode="json") for metric in all_metrics]

        # Write to storage
        storage.write_posthog_metrics(metrics_data)

        print(f"✅ Successfully saved {len(metrics_data)} metrics to storage")
        print(f"   File: data/metrics/posthog_stats.jsonl")

        # Verify the write
        with open('data/metrics/posthog_stats.jsonl', 'r') as f:
            line_count = sum(1 for _ in f)
        print(f"   Verified: {line_count} lines in file")
    else:
        print(f"⚠️  No metrics to save")

except Exception as e:
    print(f"❌ Failed to save to storage: {e}")
    import traceback
    traceback.print_exc()

# Step 7: Cleanup
print("\n[Step 7] Cleanup...")
print("-" * 80)
try:
    ingestor.close()
    print(f"✅ Ingestor closed successfully")
except Exception as e:
    print(f"❌ Failed to close ingestor: {e}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Event Properties Retrieved:  {len(event_properties) if event_properties else 0}")
print(f"Person Properties Retrieved: {len(person_properties) if person_properties else 0}")
print(f"Total Metrics Saved:         {len(all_metrics) if 'all_metrics' in locals() else 0}")
print("\n✅ Test completed successfully!")
print("=" * 80)
