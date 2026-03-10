from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI

from growth_agent.config import Settings
from growth_agent.social_listener.models import BlogOpportunity, ImageAsset, Opportunity

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return slug or "image"


def _json_candidates(text: str) -> list[str]:
    candidates = [text]
    block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if block_match:
        candidates.append(block_match.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    return candidates


class ImageBriefGenerator:
    BLOG_PROMPT = """You are PuppyOne's visual editor for SEO blog covers.

Output JSON only:
{
  "visual_direction": "one short label",
  "visual_concept": "one sentence",
  "headline": "short headline",
  "supporting_copy": ["support line 1", "support line 2"],
  "prompt": "final image prompt",
  "negative_prompt": "negative prompt",
  "palette": ["color 1", "color 2", "color 3"],
  "layout_note": "short layout note",
  "size": "1328*1328"
}

Article brief:
Title: {title}
Target keyword: {target_keyword}
Search intent: {search_intent}
Blog angle: {blog_angle}
Why it matters: {reason}
Secondary keywords: {secondary_keywords}
Outline: {outline}
Source summary: {source_summary}
"""

    X_PROMPT = """You are PuppyOne's art director for X campaign graphics.

Output JSON only:
{
  "visual_direction": "short label",
  "visual_concept": "one sentence",
  "headline": "short hook headline",
  "supporting_copy": ["support line 1", "support line 2"],
  "prompt": "final image prompt",
  "negative_prompt": "negative prompt",
  "palette": ["color 1", "color 2", "color 3"],
  "layout_note": "short layout note",
  "size": "1536*864"
}

Tweet draft:
Suggested tweet: {suggested_tweet}
Why it works: {reason}
Source title: {source_title}
Source summary: {source_summary}
Author/source: {source_author} / {source_name}
"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate_blog_cover(self, opportunity: BlogOpportunity) -> ImageAsset:
        prompt = self.BLOG_PROMPT.format(
            title=_truncate(opportunity.suggested_title or opportunity.source_content.get("title", ""), 180),
            target_keyword=_truncate(opportunity.target_keyword, 80),
            search_intent=_truncate(opportunity.search_intent, 40),
            blog_angle=_truncate(opportunity.blog_angle, 280),
            reason=_truncate(opportunity.reason, 280),
            secondary_keywords=_truncate(", ".join(opportunity.secondary_keywords[:6]), 220),
            outline=_truncate(" | ".join(opportunity.outline[:6]), 320),
            source_summary=_truncate(opportunity.source_content.get("content", ""), 600),
        )
        payload = self._complete(prompt)
        return self._build_asset(payload, "blog_cover", "1328*1328")

    def generate_x_post(self, opportunity: Opportunity) -> ImageAsset:
        source_content = opportunity.source_content or {}
        prompt = self.X_PROMPT.format(
            suggested_tweet=_truncate(opportunity.suggested_tweet, 420),
            reason=_truncate(opportunity.reason, 260),
            source_title=_truncate(source_content.get("title", ""), 180),
            source_summary=_truncate(source_content.get("content", ""), 500),
            source_author=_truncate(source_content.get("author", ""), 80),
            source_name=_truncate(source_content.get("source", ""), 80),
        )
        payload = self._complete(prompt)
        return self._build_asset(payload, "x_post", "1536*864")

    def _complete(self, prompt: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=min(self.settings.llm_temperature + 0.1, 0.5),
            max_tokens=900,
        )
        text = (response.choices[0].message.content or "").strip()
        for candidate in _json_candidates(text):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        raise ValueError("Failed to parse image brief JSON")

    def _build_asset(self, payload: dict[str, Any], asset_type: str, default_size: str) -> ImageAsset:
        supporting_copy = payload.get("supporting_copy") or []
        if isinstance(supporting_copy, str):
            supporting_copy = [line.strip() for line in supporting_copy.split("\n") if line.strip()]
        palette = payload.get("palette") or []
        if isinstance(palette, str):
            palette = [part.strip() for part in palette.split(",") if part.strip()]
        size = str(payload.get("size", "")).strip()
        if not re.fullmatch(r"\d+\*\d+", size):
            size = default_size
        return ImageAsset(
            asset_type=asset_type,
            visual_direction=_truncate(str(payload.get("visual_direction", "")).strip(), 80),
            visual_concept=_truncate(str(payload.get("visual_concept", "")).strip(), 240),
            headline=_truncate(str(payload.get("headline", "")).strip(), 140),
            supporting_copy=[_truncate(str(item).strip(), 120) for item in supporting_copy[:3] if str(item).strip()],
            prompt=_truncate(str(payload.get("prompt", "")).strip(), 790),
            negative_prompt=_truncate(str(payload.get("negative_prompt", "")).strip(), 490),
            palette=[_truncate(str(item).strip(), 40) for item in palette[:6] if str(item).strip()],
            layout_note=_truncate(str(payload.get("layout_note", "")).strip(), 180),
            size=size,
        )


class QwenImageGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.dashscope_api_key
        self.base_url = settings.dashscope_base_url
        self.model = settings.social_listener_image_model
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for rendered images")

    def render(self, asset: ImageAsset, output_dir: Path, file_stem: str, n: int = 1) -> ImageAsset:
        endpoint = self.base_url.rstrip("/") + "/services/aigc/multimodal-generation/generation"
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": {"messages": [{"role": "user", "content": [{"text": asset.prompt}]}]},
                "parameters": {
                    "negative_prompt": asset.negative_prompt or " ",
                    "size": asset.size,
                    "n": max(1, min(int(n), 6)),
                    "prompt_extend": False,
                    "watermark": False,
                },
            },
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        choices = (((payload.get("output") or {}).get("choices")) or [])
        content = (((choices[0] or {}).get("message")) or {}).get("content") or []
        image_urls = [item.get("image") for item in content if isinstance(item, dict) and item.get("image")]
        if not image_urls:
            raise ValueError("Image API response did not include image URLs")

        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[str] = []
        for index, image_url in enumerate(image_urls, start=1):
            file_path = output_dir / f"{_slugify(file_stem)}_{index}.png"
            download = requests.get(image_url, timeout=120)
            download.raise_for_status()
            file_path.write_bytes(download.content)
            saved_paths.append(str(file_path.resolve()))

        asset.image_urls = image_urls
        asset.image_paths = saved_paths
        return asset
