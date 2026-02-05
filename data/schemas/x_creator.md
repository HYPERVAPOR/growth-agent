# XCreator Schema

## Description

Represents a subscribed X/Twitter creator for content ingestion.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | X user numeric ID (must be numeric) |
| username | string | Yes | Username handle (@username) |
| followers_count | integer | Yes | Number of followers (>= 0) |
| subscribed_at | datetime | Yes | ISO 8601 timestamp when subscribed |
| last_fetched_at | datetime | No | ISO 8601 timestamp of last successful fetch |

## Example

```json
{
  "id": "1234567890",
  "username": "elonmusk",
  "followers_count": 1000000,
  "subscribed_at": "2026-02-05T10:00:00Z",
  "last_fetched_at": "2026-02-05T12:00:00Z"
}
```

## Storage

- File: `data/subscriptions/x_creators.jsonl`
- Format: JSONL (one JSON object per line)
- Operations: Append-only, update last_fetched_at on fetch

## Notes

- The `id` field must be numeric (validation enforced)
- Usernames should not include the @ symbol
- `last_fetched_at` is updated automatically after successful fetch
