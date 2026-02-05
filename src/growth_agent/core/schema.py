"""
Pydantic schema definitions for all entities in the growth-agent system.

This module defines all data models with validation for the file-system database.
"""

from datetime import datetime, UTC
from typing import Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# === Subscription Schemas ===


class XCreator(BaseModel):
    """X/Twitter creator subscription."""

    id: str = Field(..., description="X user numeric ID")
    username: str = Field(..., min_length=1, max_length=50, description="Username (@handle)")
    followers_count: int = Field(..., ge=0, description="Number of followers")
    subscribed_at: datetime = Field(description="When this creator was subscribed")
    last_fetched_at: Optional[datetime] = Field(default=None, description="Last successful fetch time")

    @field_validator("id")
    @classmethod
    def validate_numeric_id(cls, v: str) -> str:
        """Ensure ID is numeric."""
        if not v.isdigit():
            raise ValueError("X creator ID must be numeric")
        return v


class RSSFeed(BaseModel):
    """RSS feed subscription."""

    id: str = Field(..., description="UUID v4 for this feed")
    url: str = Field(..., description="Feed URL")
    title: str = Field(..., min_length=1, max_length=200, description="Feed title")
    category: Optional[str] = Field(default=None, description="Content category")
    language: Optional[str] = Field(
        default="en",
        pattern="^[a-z]{2}$",
        description="ISO 639-1 language code",
    )
    update_frequency: Optional[str] = Field(default=None, description="Expected update frequency")
    subscribed_at: datetime = Field(description="When this feed was subscribed")
    last_fetched_at: Optional[datetime] = Field(default=None, description="Last successful fetch time")
    status: Literal["active", "inactive"] = Field(default="active", description="Subscription status")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        from urllib.parse import urlparse

        result = urlparse(v)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        if result.scheme not in ["http", "https"]:
            raise ValueError("URL must use HTTP or HTTPS")
        return v


# === Inbox Schemas ===


class InboxItemBase(BaseModel):
    """Base fields for all inbox items (X and RSS)."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID in this system")
    source: Literal["x", "rss"] = Field(..., description="Content source")
    original_id: str = Field(..., description="Original platform content ID")
    author_id: str = Field(..., description="Author's ID on the platform")
    author_name: str = Field(..., description="Author's display name")
    title: Optional[str] = Field(default=None, description="Content title (RSS only)")
    content: str = Field(..., min_length=1, description="Main content text")
    url: str = Field(..., description="Original URL")
    published_at: datetime = Field(description="When the content was published")
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this content was fetched"
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class XInboxItem(InboxItemBase):
    """X/Twitter specific inbox item."""

    source: Literal["x"] = "x"
    username: str = Field(..., description="Twitter username")
    reply_count: int = Field(default=0, ge=0, description="Number of replies")
    retweet_count: int = Field(default=0, ge=0, description="Number of retweets")
    like_count: int = Field(default=0, ge=0, description="Number of likes")
    quote_count: int = Field(default=0, ge=0, description="Number of quote tweets")
    view_count: Optional[int] = Field(default=None, ge=0, description="Number of views")
    media: list[str] = Field(default_factory=list, description="Media URLs")
    hashtags: list[str] = Field(default_factory=list, description="Hashtags used")


class RSSInboxItem(InboxItemBase):
    """RSS feed specific inbox item."""

    source: Literal["rss"] = "rss"
    feed_id: str = Field(..., description="Feed ID this article belongs to")
    feed_title: str = Field(..., description="Feed title")
    categories: list[str] = Field(default_factory=list, description="Article categories/tags")
    excerpt: Optional[str] = Field(default=None, description="Article summary/excerpt")


# Type alias for union
InboxItem = XInboxItem | RSSInboxItem


# === Curated Schema ===


class CuratedItem(BaseModel):
    """LLM-evaluated curated content item."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique curated item ID")
    source_id: str = Field(..., description="Reference to inbox item ID")
    score: int = Field(..., ge=0, le=100, description="Quality score (0-100)")
    summary: str = Field(..., min_length=50, max_length=500, description="AI-generated summary")
    comment: str = Field(..., min_length=30, max_length=300, description="AI comment on value")
    rank: Optional[int] = Field(default=None, ge=1, description="Rank in top K list")
    curated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When curated")

    # Preserve original content fields for reference
    url: str = Field(..., description="Original URL")
    author_name: str = Field(..., description="Author's display name")
    title: Optional[str] = Field(default=None, description="Content title (RSS only)")
    content: str = Field(..., description="Original content text")
    published_at: datetime = Field(..., description="When the content was published")
    source: Literal["x", "rss"] = Field(..., description="Content source")


# === Blog Schema ===


class BlogFrontmatter(BaseModel):
    """YAML frontmatter for blog posts."""

    title: str = Field(..., min_length=1, max_length=200, description="Blog post title")
    date: datetime = Field(..., description="Publication date")
    summary: str = Field(..., min_length=50, max_length=300, description="Brief summary")
    tags: list[str] = Field(default_factory=list, description="Tags for the post")
    author: Optional[str] = Field(default="Growth Agent", description="Author name")


class BlogPost(BaseModel):
    """Generated blog post with frontmatter and markdown content."""

    id: str = Field(..., description="Unique blog post ID")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly slug")
    frontmatter: BlogFrontmatter = Field(..., description="YAML frontmatter")
    content: str = Field(..., min_length=1, description="Markdown body content")
    source_items: list[str] = Field(default_factory=list, description="Curated item IDs used")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When generated")


# === Workflow A Schema (GitHub Issues) ===


class GitHubIssue(BaseModel):
    """GitHub issue data for Workflow A."""

    id: int = Field(..., ge=1, description="Issue number")
    node_id: str = Field(..., description="GitHub node ID")
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue description")
    state: Literal["open", "closed"] = Field(..., description="Issue state")
    author: str = Field(..., description="Issue author username")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    closed_at: Optional[datetime] = Field(default=None, description="Closing time")
    url: str = Field(..., description="Issue URL")


# === Workflow C Schema (Social Media Metrics) ===


class MetricStat(BaseModel):
    """Social media engagement metrics for Workflow C."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique metric record ID")
    platform: Literal["x", "linkedin"] = Field(..., description="Social platform")
    content_type: Literal["post", "article"] = Field(..., description="Content format")
    content_id: str = Field(..., description="Platform content ID")
    url: str = Field(..., description="Content URL")
    impressions: Optional[int] = Field(default=None, ge=0, description="View/impression count")
    engagements: Optional[int] = Field(default=None, ge=0, description="Total engagements")
    likes: Optional[int] = Field(default=None, ge=0, description="Like count")
    retweets: Optional[int] = Field(default=None, ge=0, description="Retweet/share count")
    replies: Optional[int] = Field(default=None, ge=0, description="Reply count")
    clicks: Optional[int] = Field(default=None, ge=0, description="Click count")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When recorded")


# === Workflow Execution Results ===


class WorkflowResult(BaseModel):
    """Result of workflow execution."""

    success: bool = Field(..., description="Whether workflow completed successfully")
    items_processed: int = Field(default=0, ge=0, description="Number of items processed")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


# === LLM Response Models ===


class ContentEvaluation(BaseModel):
    """LLM evaluation response for content curation."""

    score: int = Field(..., ge=0, le=100, description="Quality score 0-100")
    summary: str = Field(..., min_length=50, max_length=500, description="Core insights summary")
    comment: str = Field(..., min_length=30, max_length=300, description="Why this content matters")
