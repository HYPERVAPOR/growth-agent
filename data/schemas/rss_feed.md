# RSSFeed Schema

## Description

Represents a subscribed RSS/Atom feed for content ingestion.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | UUID v4 identifier for this feed |
| url | string | Yes | Feed URL (HTTP/HTTPS) |
| title | string | Yes | Feed title |
| category | string | No | Content category |
| language | string | No | ISO 639-1 language code (default: "en") |
| update_frequency | string | No | Expected update frequency (e.g., "daily") |
| subscribed_at | datetime | Yes | ISO 8601 timestamp when subscribed |
| last_fetched_at | datetime | No | ISO 8601 timestamp of last successful fetch |
| status | string | No | "active" or "inactive" (default: "active") |

## Example

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "url": "https://example.com/feed.xml",
  "title": "Tech Blog",
  "category": "technology",
  "language": "en",
  "update_frequency": "daily",
  "subscribed_at": "2026-02-05T10:00:00Z",
  "last_fetched_at": "2026-02-05T12:00:00Z",
  "status": "active"
}
```

## Storage

- File: `data/subscriptions/rss_feeds.jsonl`
- Format: JSONL (one JSON object per line)
- Operations: Append-only, update last_fetched_at on fetch

## Notes

- URL validation enforced (must be HTTP or HTTPS)
- Language code must be 2-letter ISO 639-1 format
- Status field allows disabling feeds without deletion
