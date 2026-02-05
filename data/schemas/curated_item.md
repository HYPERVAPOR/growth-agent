# CuratedItem Schema

## Description

Represents content that has been evaluated and scored by the LLM. High-quality items selected for blog generation.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique curated item ID (UUID v4) |
| source_id | string | Yes | Reference to inbox item ID |
| score | integer | Yes | Quality score (0-100) |
| summary | string | Yes | AI-generated summary (50-500 chars) |
| comment | string | Yes | AI comment on value (30-300 chars) |
| rank | integer | No | Rank in top K list |
| curated_at | datetime | Yes | ISO 8601 timestamp when curated |
| **url** | **string** | **Yes** | **Original URL (preserved from inbox)** |
| **author_name** | **string** | **Yes** | **Author's display name (preserved from inbox)** |
| **title** | **string** | **No** | **Content title (preserved from inbox)** |
| **content** | **string** | **Yes** | **Original content text (preserved from inbox)** |
| **published_at** | **datetime** | **Yes** | **When published (preserved from inbox)** |
| **source** | **string** | **Yes** | **Content source: "x" or "rss"** |

## Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_id": "original-inbox-item-id",
  "score": 85,
  "summary": "This article discusses breakthrough AI technology...",
  "comment": "High value content with unique insights on LLM scaling laws",
  "rank": 1,
  "curated_at": "2026-02-05T14:30:00Z",
  "url": "https://twitter.com/elonmusk/status/1234567890",
  "author_name": "Elon Musk",
  "title": null,
  "content": "Original tweet text or article content here...",
  "published_at": "2026-02-05T12:00:00Z",
  "source": "x"
}
```

## Storage

- File: `data/curated/{YYYY-MM-DD}_ranked.jsonl`
- Format: JSONL (one JSON object per line)
- Lifecycle: Created daily, archived after blog generation

## Scoring Guidelines

- **90-100**: Exceptional, must-read content with unique insights
- **75-89**: High-quality, valuable content
- **60-74**: Good content with useful information
- **40-59**: Average content, some value but not exceptional
- **0-39**: Low quality, irrelevant, or superficial

## Notes

- Score range enforced (0-100)
- Only items with score >= threshold are included
- Ranked by score (descending) before filtering to top K
- Archived to `curated/archives/` after blog generation
