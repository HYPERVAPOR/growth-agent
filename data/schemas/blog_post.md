# BlogPost Schema

## Description

Generated blog post with YAML frontmatter and markdown content.

## Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Blog post title (1-200 chars) |
| date | datetime | Yes | Publication date (ISO 8601) |
| summary | string | Yes | Brief summary (50-300 chars) |
| tags | array | No | Tags for the post (default: []) |
| author | string | No | Author name (default: "Growth Agent") |

## Content Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique blog post ID |
| slug | string | Yes | URL-friendly slug (1-100 chars) |
| frontmatter | object | Yes | YAML frontmatter data |
| content | string | Yes | Markdown body content |
| source_items | array | Yes | List of curated item IDs used |
| generated_at | datetime | Yes | ISO 8601 timestamp when generated |

## Example

```markdown
---
title: "AI Insights: Key Developments in February 2026"
date: 2026-02-05T15:00:00Z
summary: "Daily curated insights on AI and technology"
tags: ["AI", "Technology", "LLMs"]
author: "Growth Agent"
---

# AI Insights: Key Developments in February 2026

Introduction paragraph...

## Key Insight 1

Content...

## Key Insight 2

Content...

## Conclusion

Conclusion paragraph...
```

## Storage

- File: `data/blogs/{ID}_{SLUG}.md`
- Format: Markdown with YAML frontmatter
- Lifecycle: Permanent (archived with git)

## File Naming

- Pattern: `{ID}_{SLUG}.md`
- ID: First 8 characters of UUID
- Slug: URL-safe version of title

## Notes

- Frontmatter separated by `---` delimiters
- Content in GitHub-flavored markdown
- Suitable for direct deployment to static site generators
- Version controlled with git for history
