from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from growth_agent.social_listener.models import BlogOpportunity, Opportunity


def _compact_line(label: str, value: str) -> str:
    return f"{label}: {(value or 'N/A').strip()}"


def _truncate(text: str, limit: int) -> str:
    value = " ".join((text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def build_social_text_report(opportunities: list[Opportunity], generated_at: datetime) -> str:
    lines = [
        "PuppyOne Social Opportunities",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"High-value opportunities: {len(opportunities)}",
        "Score | Author | Core angle",
    ]
    for opp in opportunities:
        author = (opp.source_content or {}).get("author", "Unknown")
        lines.append(f"{opp.score}/10 | {author} | {_truncate(opp.reason, 48)}")

    lines.append("Details")
    for index, opp in enumerate(opportunities, start=1):
        source = opp.source_content or {}
        lines.append(f"{index}. Score: {opp.score}/10 | Author: {source.get('author', 'Unknown')}")
        lines.append(_compact_line("Angle", opp.reason))
        lines.append(_compact_line("Suggested tweet", opp.suggested_tweet))
        lines.append(_compact_line("Link", source.get("link", "N/A")))
        if opp.image_asset:
            asset = opp.image_asset
            lines.append(_compact_line("Image direction", asset.get("visual_direction", "N/A")))
            paths = asset.get("image_paths") or []
            if paths:
                lines.append(_compact_line("Image files", ", ".join(paths)))
    lines.append("Reply with x1/x2/... to regenerate a social image.")
    return "\n".join(lines)


def build_blog_text_report(opportunities: list[BlogOpportunity], generated_at: datetime) -> str:
    lines = [
        "PuppyOne Blog Materials",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Selected blog ideas: {len(opportunities)}",
        "Score | Title | Keyword | Source",
    ]
    for opp in opportunities:
        source = opp.source_content or {}
        lines.append(
            f"{opp.score}/10 | {_truncate(opp.suggested_title, 36)} | "
            f"{_truncate(opp.target_keyword, 24)} | {_truncate(source.get('source', 'Unknown'), 18)}"
        )

    lines.append("Details")
    for index, opp in enumerate(opportunities, start=1):
        source = opp.source_content or {}
        lines.append(f"{index}. Score: {opp.score}/10 | Title: {_truncate(opp.suggested_title, 120)}")
        lines.append(_compact_line("Target keyword", opp.target_keyword))
        lines.append(_compact_line("Search intent", opp.search_intent))
        lines.append(_compact_line("Angle", opp.blog_angle))
        lines.append(_compact_line("Reason", opp.reason))
        lines.append(_compact_line("Link", source.get("link", "N/A")))
        if opp.outline:
            lines.append(_compact_line("Outline", " | ".join(opp.outline)))
        if opp.image_asset:
            asset = opp.image_asset
            lines.append(_compact_line("Cover direction", asset.get("visual_direction", "N/A")))
            paths = asset.get("image_paths") or []
            if paths:
                lines.append(_compact_line("Cover files", ", ".join(paths)))
    lines.append("Reply with b1/b2/... to regenerate a blog cover.")
    return "\n".join(lines)


def save_social_report(opportunities: list[Opportunity], reports_dir: Path, run_id: str) -> tuple[Path, Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now()
    json_path = reports_dir / f"puppyone_opportunities_{run_id}.json"
    md_path = reports_dir / f"puppyone_opportunities_{run_id}.md"
    txt_path = reports_dir / f"puppyone_opportunities_{run_id}.txt"
    json_path.write_text(json.dumps([opp.to_dict() for opp in opportunities], ensure_ascii=False, indent=2), encoding="utf-8")
    report = build_social_text_report(opportunities, generated_at)
    md_path.write_text(report + "\n", encoding="utf-8")
    txt_path.write_text(report + "\n", encoding="utf-8")
    return json_path, md_path, txt_path


def save_blog_report(opportunities: list[BlogOpportunity], reports_dir: Path, run_id: str) -> tuple[Path, Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now()
    json_path = reports_dir / f"puppyone_blog_materials_{run_id}.json"
    md_path = reports_dir / f"puppyone_blog_materials_{run_id}.md"
    txt_path = reports_dir / f"puppyone_blog_materials_{run_id}.txt"
    json_path.write_text(json.dumps([opp.to_dict() for opp in opportunities], ensure_ascii=False, indent=2), encoding="utf-8")
    report = build_blog_text_report(opportunities, generated_at)
    md_path.write_text(report + "\n", encoding="utf-8")
    txt_path.write_text(report + "\n", encoding="utf-8")
    return json_path, md_path, txt_path


def latest_report_path(reports_dir: Path, kind: str) -> Path:
    pattern = "puppyone_opportunities_*.json" if kind == "x" else "puppyone_blog_materials_*.json"
    candidates = sorted(reports_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("No social listener report found yet")
    return candidates[0]
