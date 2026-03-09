#!/usr/bin/env python
"""
Minimal test for PostHog API key validity.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from growth_agent.config import Settings

# Load settings (includes .env file)
settings = Settings()
API_KEY = settings.posthog_api_key
HOST = settings.posthog_host
PROJECT_ID = settings.posthog_project_id

print("=" * 60)
print("PostHog API Key Test")
print("=" * 60)

if not API_KEY:
    print("✗ Error: POSTHOG_API_KEY not found in environment")
    sys.exit(1)

if not PROJECT_ID:
    print("✗ Error: POSTHOG_PROJECT_ID not found in environment")
    sys.exit(1)

print(f"\nConfiguration:")
print(f"  API Key: {API_KEY[:15]}...")
print(f"  Host: {HOST}")
print(f"  Project ID: {PROJECT_ID}")

# Test 1: Simple API call - Get project info
print("\n[Test 1] Fetching project info...")
try:
    response = httpx.get(
        f"https://{HOST}/api/projects/{PROJECT_ID}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10.0
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Project name: {data.get('name', 'N/A')}")
        print(f"   Project ID: {data.get('id', 'N/A')}")
        org = data.get('organization')
        if isinstance(org, dict):
            print(f"   Organization: {org.get('name', 'N/A')}")
        else:
            print(f"   Organization: {org}")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 2: Try to fetch insights (most common endpoint)
print("\n[Test 2] Fetching insights (requires proper permissions)...")
try:
    response = httpx.get(
        f"https://{HOST}/api/projects/{PROJECT_ID}/insights/",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10.0
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data.get('results', []))} insights")
    elif response.status_code == 403:
        print(f"⚠️  Forbidden (403) - API Key lacks 'insights:read' permission")
        print(f"   This is expected for Personal API Keys on some plans")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"  Response: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Try to fetch events
print("\n[Test 3] Fetching recent events...")
try:
    response = httpx.get(
        f"https://{HOST}/api/projects/{PROJECT_ID}/events/",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"limit": 1},
        timeout=10.0
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Events endpoint accessible")
    elif response.status_code == 401:
        print(f"⚠️  Unauthorized (401) - Wrong API Key type or insufficient permissions")
        print(f"   Note: Make sure to use Project API Key, not Personal API Key")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"  Response: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
