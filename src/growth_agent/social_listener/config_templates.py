from __future__ import annotations

import json
from pathlib import Path


SOCIAL_SOURCES = {
    "sources": [
        {
            "name": "Sam Altman",
            "url": "https://api.xgo.ing/rss/user/e30d4cd223f44bed9d404807105c8927",
            "type": "twitter_rss",
        },
        {
            "name": "OpenAI Developers",
            "url": "https://api.xgo.ing/rss/user/971dc1fc90da449bac23e5fad8a33d55",
            "type": "twitter_rss",
        },
        {
            "name": "Anthropic",
            "url": "https://api.xgo.ing/rss/user/fc28a211471b496682feff329ec616e5",
            "type": "twitter_rss",
        },
    ]
}

BLOG_SOURCES = {
    "sources": [
        {"name": "Simon Willison", "url": "https://simonwillison.net/atom/entries/", "type": "atom"},
        {"name": "GitHub Blog", "url": "https://github.blog/feed/", "type": "rss"},
        {"name": "LangChain Blog", "url": "https://blog.langchain.com/rss/", "type": "rss"},
        {"name": "Vercel Blog", "url": "https://vercel.com/atom", "type": "atom"},
        {"name": "Martin Fowler", "url": "https://martinfowler.com/bliki/bliki.atom", "type": "atom"},
        {"name": "Google Search Central", "url": "https://feeds.feedburner.com/blogspot/amDG", "type": "rss"},
        {"name": "Cloudflare Blog", "url": "https://blog.cloudflare.com/rss/", "type": "rss"},
        {"name": "MCP Specification Releases", "url": "https://github.com/modelcontextprotocol/specification/releases.atom", "type": "atom"},
    ]
}


def ensure_default_configs(config_dir: Path) -> tuple[Path, Path]:
    config_dir.mkdir(parents=True, exist_ok=True)
    social_path = config_dir / "sources.json"
    blog_path = config_dir / "blog_sources.json"
    if not social_path.exists():
        social_path.write_text(json.dumps(SOCIAL_SOURCES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not blog_path.exists():
        blog_path.write_text(json.dumps(BLOG_SOURCES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return social_path, blog_path
