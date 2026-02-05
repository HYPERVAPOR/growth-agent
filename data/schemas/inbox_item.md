# InboxItem Schema

## Description

Base schema for content ingested from X/Twitter and RSS feeds. Unified storage format for all sources.

## Common Fields (All Sources)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique ID in this system (UUID v4) |
| source | string | Yes | "x" or "rss" |
| original_id | string | Yes | Original platform content ID |
| author_id | string | Yes | Author's ID on the platform |
| author_name | string | Yes | Author's display name |
| title | string | No | Content title (RSS only) |
| content | string | Yes | Main content text |
| url | string | Yes | Original URL |
| published_at | datetime | Yes | ISO 8601 timestamp when published |
| fetched_at | datetime | Yes | ISO 8601 timestamp when fetched |
| metadata | object | No | Additional metadata |

## X/Twitter Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Twitter username |
| reply_count | integer | Yes | Number of replies (default: 0) |
| retweet_count | integer | Yes | Number of retweets (default: 0) |
| like_count | integer | Yes | Number of likes (default: 0) |
| quote_count | integer | Yes | Number of quote tweets (default: 0) |
| view_count | integer | No | Number of views |
| media | array | Yes | List of media URLs (default: []) |
| hashtags | array | Yes | List of hashtags (default: []) |

## RSS Specific Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| feed_id | string | Yes | Feed ID this article belongs to |
| feed_title | string | Yes | Feed title |
| categories | array | Yes | Article categories/tags (default: []) |
| excerpt | string | No | Article summary/excerpt |

## Storage

- File: `data/inbox/items.jsonl`
- Format: JSONL (one JSON object per line)
- Lifecycle: Ingested → Curated → Deleted

## Notes

- All items are deleted after curation to maintain inbox as a staging area
- Vector index created in LanceDB for all inbox items
- Both X and RSS items share common base fields
