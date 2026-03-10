from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ContentItem:
    title: str
    author: str
    link: str
    content: str
    pub_date: datetime
    source: str
    content_type: str = "rss"
    raw_data: dict[str, Any] | None = None


@dataclass
class Opportunity:
    score: int
    reason: str
    suggested_tweet: str
    source_content: dict[str, Any] | None = None
    image_asset: dict[str, Any] | None = None
    evaluated_at: str | None = None

    def __post_init__(self) -> None:
        if self.evaluated_at is None:
            self.evaluated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BlogOpportunity:
    score: int
    reason: str
    target_keyword: str
    search_intent: str
    blog_angle: str
    suggested_title: str
    secondary_keywords: list[str]
    outline: list[str]
    source_content: dict[str, Any]
    image_asset: dict[str, Any] | None = None
    evaluated_at: str | None = None

    def __post_init__(self) -> None:
        if self.evaluated_at is None:
            self.evaluated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImageAsset:
    asset_type: str
    visual_direction: str
    visual_concept: str
    headline: str
    supporting_copy: list[str]
    prompt: str
    negative_prompt: str
    palette: list[str]
    layout_note: str
    size: str
    image_paths: list[str] = field(default_factory=list)
    image_urls: list[str] = field(default_factory=list)
    generated_at: str | None = None

    def __post_init__(self) -> None:
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
