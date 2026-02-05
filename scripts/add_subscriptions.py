#!/usr/bin/env python
"""
Fetch X creator IDs and add subscriptions.
"""
import json
import os
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

import httpx

# API配置
X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY", "3fd1d69e82msh08c653ab77d98afp150fccjsn692d533a2b0b")
X_RAPIDAPI_HOST = os.getenv("X_RAPIDAPI_HOST", "twitter241.p.rapidapi.com")

# X博主用户名列表
x_usernames = [
    "OpenAI",
    "sama",
    "GoogleDeepMind",
    "demishassabis",
    "MetaAI",
    "ylecun",
    "AnthropicAI",
    "karpathy",
    "AndrewYNg",
    "DrJimFan",
    "rasbt",
    "chipro",
    "rowancheung",
    "LinusEkenstam",
    "OfficialLoganK",
    "bindureddy",
    "huggingface",
    "ClementDelangue",
    "MistralAI",
    "lexfridman",
]

# RSS源列表
rss_feeds_list = [
    ("https://openai.com/news/rss.xml", "OpenAI Blog", "technology", "en"),
    ("https://deepmind.google/blog/rss.xml", "Google DeepMind Blog", "technology", "en"),
    ("https://huggingface.co/blog/feed.xml", "Hugging Face Blog", "technology", "en"),
    ("https://research.facebook.com/feed/", "Meta AI Research", "research", "en"),
    ("https://blogs.nvidia.com/feed/", "NVIDIA Blog", "technology", "en"),
    ("https://rss.arxiv.org/rss/cs.AI", "arXiv CS.AI", "research", "en"),
    ("https://rss.arxiv.org/rss/cs.CL", "arXiv CS.CL", "research", "en"),
    ("https://bair.berkeley.edu/blog/feed.xml", "BAIR Berkeley", "research", "en"),
    ("https://ai.stanford.edu/blog/feed.xml", "Stanford AI Blog", "research", "en"),
    ("https://jalammar.github.io/feed.xml", "Jay Alammar", "blog", "en"),
    ("https://lilianweng.github.io/posts/index.xml", "Lilian Weng", "blog", "en"),
    ("https://www.deeplearning.ai/the-batch/rss/", "DeepLearning.AI", "news", "en"),
    ("https://simonwillison.net/atom/entries/", "Simon Willison", "blog", "en"),
    ("https://machinelearningmastery.com/blog/feed", "ML Mastery", "education", "en"),
    ("https://news.mit.edu/rss/topic/artificial-intelligence2", "MIT AI News", "news", "en"),
    ("https://www.bensbites.co/feed", "Ben's Bites", "newsletter", "en"),
    ("https://www.reddit.com/r/MachineLearning/.rss", "Reddit ML", "community", "en"),
    ("https://hnrss.org/newest?q=AI", "Hacker News AI", "news", "en"),
]


def get_user_id(username: str) -> str | None:
    """通过用户名获取X用户ID"""
    url = f"https://{X_RAPIDAPI_HOST}/user?username={username}"
    headers = {
        "x-rapidapi-key": X_RAPIDAPI_KEY,
        "x-rapidapi-host": X_RAPIDAPI_HOST,
    }

    try:
        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        # 解析响应获取用户ID
        # 响应结构: {"result": {"data": {"user": {"result": {"rest_id": "123"}}}}}
        rest_id = None

        # 尝试多个可能的路径
        if "result" in data:
            if "data" in data["result"]:
                if "user" in data["result"]["data"]:
                    if "result" in data["result"]["data"]["user"]:
                        rest_id = data["result"]["data"]["user"]["result"].get("rest_id")

        if rest_id:
            return rest_id

        print(f"  ✗ 无法获取 @{username} 的ID")
        return None

    except Exception as e:
        print(f"  ✗ 获取 @{username} 时出错: {e}")
        return None


def add_x_creators() -> None:
    """添加X创作者订阅"""
    print("正在获取X创作者ID...")

    creators = []
    for username in x_usernames:
        print(f"  正在获取 @{username}...")
        user_id = get_user_id(username)

        if user_id:
            creator = {
                "id": user_id,
                "username": username,
                "followers_count": 0,  # 稍后更新
                "subscribed_at": datetime.now(UTC).isoformat(),
                "last_fetched_at": None,
            }
            creators.append(creator)
            print(f"  ✓ @{username} (ID: {user_id})")

    # 保存到文件
    data_root = Path("data")
    x_creators_path = data_root / "subscriptions" / "x_creators.jsonl"

    with open(x_creators_path, "w") as f:
        for creator in creators:
            f.write(json.dumps(creator, ensure_ascii=False) + "\n")

    print(f"\n✓ 成功添加 {len(creators)} 个X创作者订阅")
    print(f"  文件: {x_creators_path}")


def add_rss_feeds() -> None:
    """添加RSS源订阅"""
    print("\n正在添加RSS源...")

    feeds = []
    for url, title, category, language in rss_feeds_list:
        feed = {
            "id": str(uuid4()),
            "url": url,
            "title": title,
            "category": category,
            "language": language,
            "update_frequency": "daily",
            "subscribed_at": datetime.now(UTC).isoformat(),
            "last_fetched_at": None,
            "status": "active",
        }
        feeds.append(feed)
        print(f"  ✓ {title}")

    # 保存到文件
    data_root = Path("data")
    rss_feeds_path = data_root / "subscriptions" / "rss_feeds.jsonl"

    with open(rss_feeds_path, "w") as f:
        for feed in feeds:
            f.write(json.dumps(feed, ensure_ascii=False) + "\n")

    print(f"\n✓ 成功添加 {len(feeds)} 个RSS源订阅")
    print(f"  文件: {rss_feeds_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("添加 Growth Agent 订阅")
    print("=" * 60)

    add_x_creators()
    add_rss_feeds()

    print("\n" + "=" * 60)
    print("订阅添加完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 运行: python -m growth_agent.main run workflow-b")
    print("  2. 或者启动调度器: python -m growth_agent.main schedule")
