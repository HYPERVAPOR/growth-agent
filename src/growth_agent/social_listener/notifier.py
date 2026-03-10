from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import requests

from growth_agent.social_listener.models import BlogOpportunity, Opportunity

logger = logging.getLogger(__name__)


class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_summary(
        self,
        social_opportunities: list[Opportunity],
        blog_opportunities: list[BlogOpportunity],
        social_report: Path | None = None,
        blog_report: Path | None = None,
    ) -> None:
        content = (
            "PuppyOne daily social listener finished.\n"
            f"Social opportunities: {len(social_opportunities)}\n"
            f"Blog ideas: {len(blog_opportunities)}"
        )
        if social_report:
            content += f"\nSocial report: `{social_report}`"
        if blog_report:
            content += f"\nBlog report: `{blog_report}`"
        self._post_json({"content": content})

    def send_social_opportunity(self, opportunity: Opportunity, index: int) -> None:
        source = opportunity.source_content or {}
        embed = {
            "title": f"Social opportunity #{index} ({opportunity.score}/10)",
            "url": source.get("link"),
            "color": 3447003,
            "fields": [
                {"name": "Source", "value": source.get("author", "Unknown"), "inline": True},
                {"name": "Angle", "value": (opportunity.reason or "N/A")[:1024], "inline": False},
                {"name": "Suggested tweet", "value": (opportunity.suggested_tweet or "N/A")[:1024], "inline": False},
            ],
            "footer": {"text": f"PuppyOne Social Listener • {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
        }
        self._post_embed_with_optional_image(embed, (opportunity.image_asset or {}).get("image_paths") or [])

    def send_blog_opportunity(self, opportunity: BlogOpportunity, index: int) -> None:
        source = opportunity.source_content or {}
        embed = {
            "title": f"Blog idea #{index} ({opportunity.score}/10)",
            "url": source.get("link"),
            "color": 3066993,
            "fields": [
                {"name": "Title", "value": (opportunity.suggested_title or "N/A")[:256], "inline": False},
                {"name": "Target keyword", "value": (opportunity.target_keyword or "N/A")[:256], "inline": True},
                {"name": "Intent", "value": (opportunity.search_intent or "N/A")[:256], "inline": True},
                {"name": "Angle", "value": (opportunity.blog_angle or "N/A")[:1024], "inline": False},
            ],
            "footer": {"text": f"PuppyOne Social Listener • {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
        }
        self._post_embed_with_optional_image(embed, (opportunity.image_asset or {}).get("image_paths") or [])

    def _post_embed_with_optional_image(self, embed: dict, image_paths: list[str]) -> None:
        existing_paths = [Path(path) for path in image_paths if Path(path).exists()]
        if not existing_paths:
            self._post_json({"embeds": [embed]})
            return

        image_path = existing_paths[0]
        embed["image"] = {"url": f"attachment://{image_path.name}"}
        with image_path.open("rb") as handle:
            response = requests.post(
                self.webhook_url,
                data={"payload_json": json.dumps({"embeds": [embed]})},
                files={"file0": (image_path.name, handle, "image/png")},
                timeout=60,
            )
        response.raise_for_status()

    def _post_json(self, payload: dict) -> None:
        response = requests.post(self.webhook_url, json=payload, timeout=30)
        response.raise_for_status()
