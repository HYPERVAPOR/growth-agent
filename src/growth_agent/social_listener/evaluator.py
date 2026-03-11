from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from growth_agent.config import Settings
from growth_agent.social_listener.models import BlogOpportunity, ContentItem, Opportunity

logger = logging.getLogger(__name__)


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


class SocialOpportunityEvaluator:
    DEFAULT_PROMPT = """You are PuppyOne's social growth lead.

PuppyOne is infrastructure that helps AI agents securely access real-world tools and data using MCP-style integrations.

Evaluate whether the following post or article is a good trigger for PuppyOne to publish an original English tweet that rides the topic.

Strong relevance signals:
- MCP, model context protocol, tool calling, agent workflows
- agent access to Gmail, Calendar, GitHub, Notion, Drive, Slack, APIs, filesystems
- auth, permissions, scopes, sandboxing, auditability, least privilege
- why agents can chat but fail at real work because they lack live data or tools
- context engineering, context file system, AI agent memory, context management
- version control for agents, rollback, snapshots, audit logs, tamper-evident logs
- multi-agent collaboration, multi-agent security, agent governance
- AI running amok, rogue agent, AI data loss, blast radius, AI out of control
- human-in-the-loop approvals, least privilege, default-deny, access control
- agentic RAG, retrieval-augmented generation, hybrid indexing, deep research
- token pressure, context churn, prompt injection, runtime isolation
- self-hosted AI, private deployment, enterprise governance, enterprise AI security

Scoring:
- 9-10: strong PuppyOne angle, highly worth posting
- 7-8: relevant enough to post with a clear angle
- 0-6: not worth posting

If score >= 7, return JSON:
{
  "score": 8,
  "reason": "Short reason why this is a good PuppyOne angle",
  "suggested_tweet": "A native-sounding original English tweet, 100-280 chars, not a reply, not overly promotional"
}

If score < 7, return null.
Return JSON or null only.

Author: {author}
Title: {title}
Content: {content}
Link: {link}
Published at: {pub_date}
"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def evaluate_batch(self, items: list[ContentItem], delay: float = 0.3) -> list[Opportunity]:
        results: list[Opportunity] = []
        for index, item in enumerate(items, start=1):
            logger.info("Evaluating social item %s/%s", index, len(items))
            result = self.evaluate_single(item)
            if result is not None:
                results.append(result)
            if index < len(items):
                time.sleep(delay)
        results.sort(key=lambda item: item.score, reverse=True)
        return results

    def evaluate_single(self, item: ContentItem) -> Opportunity | None:
        prompt = (
            self.DEFAULT_PROMPT.replace("{author}", item.author or "")
            .replace("{title}", (item.title or "")[:220])
            .replace("{content}", (item.content or "")[:1200])
            .replace("{link}", item.link or "")
            .replace("{pub_date}", item.pub_date.isoformat() if item.pub_date else "")
        )
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=min(self.settings.llm_temperature, 0.4),
            max_tokens=min(max(self.settings.llm_max_tokens, 500), 900),
        )
        text = (response.choices[0].message.content or "").strip()
        if text.lower() == "null":
            return None
        data: dict[str, Any] | None = None
        for candidate in _json_candidates(text):
            try:
                data = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not data:
            logger.warning("Failed to parse social evaluation JSON")
            return None
        score = int(data.get("score", 0))
        if score < self.settings.social_listener_social_min_score:
            return None
        return Opportunity(
            score=score,
            reason=str(data.get("reason", "")).strip(),
            suggested_tweet=str(data.get("suggested_tweet", "")).strip(),
            source_content={
                "author": item.author,
                "title": item.title,
                "link": item.link,
                "content": (item.content or "")[:700],
                "pub_date": item.pub_date.isoformat() if item.pub_date else None,
                "source": item.source,
            },
        )


class BlogSignalFilter:
    PRIMARY_KEYWORDS = [
        "model context protocol",
        "mcp",
        "agent",
        "multi-agent",
        "tool calling",
        "function calling",
        "oauth",
        "authentication",
        "authorization",
        "identity",
        "permission",
        "access control",
        "least privilege",
        "sandbox",
        "runtime isolation",
        "connector",
        "integration",
        "workflow",
        "context",
        "context engineering",
        "context file system",
        "context management",
        "memory",
        "data access",
        "private data",
        "filesystem",
        "gmail",
        "calendar",
        "github",
        "notion",
        "drive",
        "slack",
        "version control",
        "audit log",
        "audit trail",
        "tamper-evident",
        "rollback",
        "snapshot",
        "agentic rag",
        "retrieval-augmented generation",
        "rag",
        "hybrid indexing",
        "deep research",
        "enterprise governance",
        "self-hosted",
        "private deployment",
        "blast radius",
        "human-in-the-loop",
        "token pressure",
        "rogue agent",
        "ai agent security",
        "agent governance",
    ]

    HIGH_SIGNAL_SOURCES = {
        "Simon Willison",
        "GitHub Blog",
        "LangChain Blog",
        "Vercel Blog",
        "Martin Fowler",
        "Cloudflare Blog",
        "MCP Specification Releases",
        "Google Search Central",
    }

    NOISE_PATTERNS = [
        re.compile(r"\bseries [abc]\b", re.IGNORECASE),
        re.compile(r"\bfunding\b", re.IGNORECASE),
        re.compile(r"\bwe('?re| are) hiring\b", re.IGNORECASE),
        re.compile(r"\bwebinar\b", re.IGNORECASE),
        re.compile(r"\bpodcast\b", re.IGNORECASE),
        re.compile(r"\bevent\b", re.IGNORECASE),
    ]

    def __init__(self, min_words: int = 18):
        self.min_words = min_words

    def filter(self, items: list[ContentItem]) -> list[ContentItem]:
        filtered: list[ContentItem] = []
        for item in items:
            combined = " ".join([item.title or "", item.content or ""]).strip()
            lowered = combined.lower()
            if len(combined.split()) < self.min_words:
                continue
            match_count = sum(1 for keyword in self.PRIMARY_KEYWORDS if keyword in lowered)
            if item.source in self.HIGH_SIGNAL_SOURCES and match_count >= 1:
                filtered.append(item)
                continue
            if match_count >= 2:
                filtered.append(item)
                continue
            if match_count >= 1 and not any(pattern.search(combined) for pattern in self.NOISE_PATTERNS):
                filtered.append(item)
        logger.info("Filtered %s blog candidates to %s", len(items), len(filtered))
        return filtered


class BlogIdeaEvaluator:
    DEFAULT_PROMPT = """You are PuppyOne's SEO editor.

PuppyOne helps AI agents securely access real-world data and tools across systems like Gmail, Calendar, GitHub, Notion, Drive and Slack.

Assess whether this source is worth turning into a PuppyOne SEO article. Prefer:
- secure agent data access, context file system, AI agent workspace
- MCP and connector layer design, model context protocol integration
- auth, permissions, scopes, sandboxing, audit logs, tamper-evident logs
- why agents fail outside the chat window, token pressure, context churn
- RAG vs live tool access, agentic RAG, hybrid indexing, deep research
- production agent architecture and multi-tool workflows
- version control for agents, rollback, snapshots, traceable AI
- multi-agent security, enterprise AI governance, least privilege, default-deny
- AI running amok, rogue agent, blast radius, human-in-the-loop
- self-hosted AI, private deployment, enterprise governance, runtime isolation
- context engineering, context management, AI agent memory

If score >= 7, return JSON:
{
  "score": 8,
  "reason": "Why this is worth writing",
  "target_keyword": "main keyword",
  "search_intent": "informational | problem-solution | integration | comparison | security | architecture",
  "blog_angle": "Specific writing angle",
  "suggested_title": "SEO-friendly English title",
  "secondary_keywords": ["keyword 1", "keyword 2", "keyword 3"],
  "outline": ["H2 1", "H2 2", "H2 3", "H2 4", "H2 5"]
}

If score < 7, return null.
Return JSON or null only.

Source: {source}
Author: {author}
Title: {title}
Content: {content}
Link: {link}
Published at: {pub_date}
"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def evaluate_batch(self, items: list[ContentItem], delay: float = 0.3) -> list[BlogOpportunity]:
        results: list[BlogOpportunity] = []
        for index, item in enumerate(items, start=1):
            logger.info("Evaluating blog item %s/%s", index, len(items))
            result = self.evaluate_single(item)
            if result is not None:
                results.append(result)
            if index < len(items):
                time.sleep(delay)
        results.sort(key=lambda item: item.score, reverse=True)
        return results

    def evaluate_single(self, item: ContentItem) -> BlogOpportunity | None:
        prompt = (
            self.DEFAULT_PROMPT.replace("{source}", item.source or "")
            .replace("{author}", item.author or "")
            .replace("{title}", (item.title or "")[:220])
            .replace("{content}", (item.content or "")[:1600])
            .replace("{link}", item.link or "")
            .replace("{pub_date}", item.pub_date.isoformat() if item.pub_date else "")
        )
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=min(self.settings.llm_temperature, 0.3),
            max_tokens=min(max(self.settings.llm_max_tokens, 700), 1200),
        )
        text = (response.choices[0].message.content or "").strip()
        if text.lower() == "null":
            return None
        data: dict[str, Any] | None = None
        for candidate in _json_candidates(text):
            try:
                data = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not data:
            logger.warning("Failed to parse blog evaluation JSON")
            return None
        score = int(data.get("score", 0))
        if score < self.settings.social_listener_blog_min_score:
            return None
        outline = data.get("outline") or []
        if isinstance(outline, str):
            outline = [outline]
        secondary_keywords = data.get("secondary_keywords") or []
        if isinstance(secondary_keywords, str):
            secondary_keywords = [part.strip() for part in secondary_keywords.split(",") if part.strip()]
        return BlogOpportunity(
            score=score,
            reason=str(data.get("reason", "")).strip(),
            target_keyword=str(data.get("target_keyword", "")).strip(),
            search_intent=str(data.get("search_intent", "")).strip(),
            blog_angle=str(data.get("blog_angle", "")).strip(),
            suggested_title=str(data.get("suggested_title", "")).strip(),
            secondary_keywords=[str(value).strip() for value in secondary_keywords[:8] if str(value).strip()],
            outline=[str(value).strip() for value in outline[:6] if str(value).strip()],
            source_content={
                "author": item.author,
                "title": item.title,
                "link": item.link,
                "content": (item.content or "")[:700],
                "pub_date": item.pub_date.isoformat() if item.pub_date else None,
                "source": item.source,
            },
        )
