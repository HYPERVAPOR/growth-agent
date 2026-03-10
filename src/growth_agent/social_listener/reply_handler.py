from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from growth_agent.social_listener.models import BlogOpportunity, ImageAsset, Opportunity
from growth_agent.social_listener.reporter import latest_report_path

if TYPE_CHECKING:
    from growth_agent.config import Settings


def parse_selection(text: str) -> tuple[str, int]:
    match = re.fullmatch(r"([xb])\s*(\d+)", (text or "").strip().lower())
    if not match:
        raise ValueError("Invalid selection. Use x1 or b1 style commands.")
    return match.group(1), int(match.group(2))


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: list[dict]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_social(item: dict) -> Opportunity:
    return Opportunity(
        score=item.get("score", 0),
        reason=item.get("reason", ""),
        suggested_tweet=item.get("suggested_tweet", ""),
        source_content=item.get("source_content") or {},
        image_asset=item.get("image_asset"),
        evaluated_at=item.get("evaluated_at"),
    )


def _build_blog(item: dict) -> BlogOpportunity:
    return BlogOpportunity(
        score=item.get("score", 0),
        reason=item.get("reason", ""),
        target_keyword=item.get("target_keyword", ""),
        search_intent=item.get("search_intent", ""),
        blog_angle=item.get("blog_angle", ""),
        suggested_title=item.get("suggested_title", ""),
        secondary_keywords=item.get("secondary_keywords") or [],
        outline=item.get("outline") or [],
        source_content=item.get("source_content") or {},
        image_asset=item.get("image_asset"),
        evaluated_at=item.get("evaluated_at"),
    )


def handle_selection(settings: Settings, reports_dir: Path, selection: str, force: bool = False) -> str:
    kind, index = parse_selection(selection)
    report_path = latest_report_path(reports_dir, kind)
    items = _load_json(report_path)
    if index < 1 or index > len(items):
        raise IndexError(f"Selection out of range: 1..{len(items)}")

    item = items[index - 1]
    asset = None if force else _existing_asset(item)
    if asset is None:
        asset = _generate_asset(settings, reports_dir, report_path, kind, item, index)
        item["image_asset"] = asset.to_dict()
        items[index - 1] = item
        _save_json(report_path, items)
    return _render_response(kind, index, asset)


def _existing_asset(item: dict) -> ImageAsset | None:
    payload = item.get("image_asset") or {}
    image_paths = [path for path in payload.get("image_paths") or [] if Path(path).exists()]
    if not image_paths:
        return None
    payload["image_paths"] = image_paths
    return ImageAsset(**payload)


def _generate_asset(
    settings: Settings,
    reports_dir: Path,
    report_path: Path,
    kind: str,
    item: dict,
    index: int,
) -> ImageAsset:
    from growth_agent.social_listener.image_generator import ImageBriefGenerator, QwenImageGenerator

    brief_generator = ImageBriefGenerator(settings)
    renderer = QwenImageGenerator(settings)
    image_dir = reports_dir / f"{report_path.stem}_images"
    if kind == "x":
        opportunity = _build_social(item)
        asset = brief_generator.generate_x_post(opportunity)
        label = opportunity.source_content.get("author", f"x-{index}")
        renderer.render(asset, image_dir, f"x_{index}_{label}", 1)
        return asset

    opportunity = _build_blog(item)
    asset = brief_generator.generate_blog_cover(opportunity)
    label = opportunity.suggested_title or f"b-{index}"
    renderer.render(asset, image_dir, f"b_{index}_{label}", 1)
    return asset


def _render_response(kind: str, index: int, asset: ImageAsset) -> str:
    label = "social image" if kind == "x" else "blog cover"
    lines = [f"Generated {label} {index}"]
    if asset.headline:
        lines.append(f"Headline: {asset.headline}")
    if asset.visual_direction:
        lines.append(f"Direction: {asset.visual_direction}")
    for image_path in asset.image_paths:
        lines.append(f"File: {image_path}")
        lines.append(f"![{kind}{index}]({image_path})")
    return "\n".join(lines)
