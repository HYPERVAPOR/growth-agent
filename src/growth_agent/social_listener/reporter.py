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
    ]

    for index, opp in enumerate(opportunities, start=1):
        source = opp.source_content or {}
        author = source.get("author") or "Unknown"
        link = source.get("link", "N/A")
        pub_date = source.get("pub_date") or source.get("published_at") or source.get("published") or "N/A"
        source_summary = source.get("content") or source.get("summary") or ""

        lines.append("")
        lines.append(f"##{opp.score}/10 {index}. {author}")
        lines.append(f"**链接:** [{link}]({link})")
        lines.append(f"**发布时间:** {pub_date}")
        lines.append("**匹配原因:**")
        lines.append(opp.reason or "N/A")
        lines.append("**原创推文（可直接发布）:**")
        lines.append(f"> {opp.suggested_tweet or 'N/A'}")
        if source_summary:
            lines.append("**原文摘要:**")
            lines.append(_truncate(source_summary, 300))
        if opp.image_asset:
            asset = opp.image_asset
            lines.append(_compact_line("Image direction", asset.get("visual_direction", "N/A")))
            paths = asset.get("image_paths") or []
            if paths:
                lines.append(_compact_line("Image files", ", ".join(paths)))

    lines.append("")
    lines.append("Reply with x1/x2/... to regenerate a social image.")
    return "\n".join(lines)


def build_blog_text_report(opportunities: list[BlogOpportunity], generated_at: datetime) -> str:
    lines = [
        "PuppyOne Blog Materials",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Selected blog ideas: {len(opportunities)}",
    ]

    for index, opp in enumerate(opportunities, start=1):
        source = opp.source_content or {}
        source_name = source.get("source") or source.get("author") or "Unknown"
        source_author = source.get("author") or source_name
        link = source.get("link", "N/A")
        published = source.get("pub_date") or source.get("published_at") or source.get("published") or "N/A"

        lines.append("")
        lines.append(f"##{opp.score}/10 {index}. {opp.suggested_title or 'Untitled'}")
        lines.append(f"- 目标关键词: {opp.target_keyword or 'N/A'}")
        lines.append(f"- 搜索意图: {opp.search_intent or 'N/A'}")
        lines.append(f"- 写作角度: {opp.blog_angle or 'N/A'}")
        lines.append(f"- 来源: {source_author} / {source_name}")
        lines.append(f"- 原文链接: {link}")
        lines.append(f"- 发布时间: {published}")
        if opp.secondary_keywords:
            lines.append(f"- 次关键词: {', '.join(opp.secondary_keywords)}")
        lines.append("**为什么值得写**")
        lines.append(opp.reason or "N/A")
        if opp.outline:
            lines.append("**建议结构**")
            for step in opp.outline:
                lines.append(f"- {step}")
        source_summary = source.get("content") or source.get("summary") or ""
        if source_summary:
            lines.append("**原文摘要**")
            lines.append(_truncate(source_summary, 300))
        if opp.image_asset:
            asset = opp.image_asset
            lines.append(_compact_line("Cover direction", asset.get("visual_direction", "N/A")))
            paths = asset.get("image_paths") or []
            if paths:
                lines.append(_compact_line("Cover files", ", ".join(paths)))

    lines.append("")
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
