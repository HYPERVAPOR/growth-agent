import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


def _normalize_post(
    raw: Dict[str, Any],
    *,
    fallback_subreddit: Optional[str] = None,
    permalink_base: str = "https://www.reddit.com",
) -> Optional[Dict[str, Any]]:
    """
    Convert various RapidAPI/Reddit shapes into the internal post schema:
    {post_id,title,url,subreddit,upvotes,comments_count,created_utc}
    """
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    if not isinstance(data, dict):
        return None

    post_id = data.get("id") or data.get("post_id") or data.get("name")
    title = data.get("title") or ""
    if not post_id or not title:
        return None

    subreddit = data.get("subreddit") or fallback_subreddit or ""
    created_utc = data.get("created_utc") or data.get("createdUtc") or data.get(
        "created"
    )

    permalink = data.get("permalink") or data.get("url") or ""
    if isinstance(permalink, str) and permalink.startswith("/"):
        url = f"{permalink_base}{permalink}"
    else:
        url = permalink if isinstance(permalink, str) else ""

    upvotes = (
        data.get("ups")
        or data.get("upvotes")
        or data.get("score")
        or data.get("like_count")
        or 0
    )
    comments_count = (
        data.get("num_comments") or data.get("comments_count") or data.get("comments") or 0
    )

    try:
        created_ts = float(created_utc) if created_utc is not None else 0.0
    except Exception:
        created_ts = 0.0

    return {
        "post_id": str(post_id),
        "title": str(title),
        "url": str(url),
        "subreddit": str(subreddit),
        "upvotes": upvotes,
        "comments_count": comments_count,
        "created_utc": created_ts,
    }


def _extract_listing_items(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept common listing response shapes:
    - Reddit listing JSON: {data:{children:[{data:{...}}, ...]}}
    - RapidAPI wrapper: {posts:[...]} or {data:[...]} or list[...]
    """
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]

    if not isinstance(payload, dict):
        return []

    if isinstance(payload.get("posts"), list):
        return [p for p in payload["posts"] if isinstance(p, dict)]

    data = payload.get("data")
    if isinstance(data, list):
        return [p for p in data if isinstance(p, dict)]

    if isinstance(data, dict):
        # Handle {data: {posts: [...]}} shape (e.g. reddit34 RapidAPI)
        if isinstance(data.get("posts"), list):
            return [p for p in data["posts"] if isinstance(p, dict)]

        if isinstance(data.get("children"), list):
            children = [c for c in data["children"] if isinstance(c, dict)]
            # children may be {data:{...}} already; keep as dicts for normalization
            return children

    # last resort: some APIs return {items:[...]}
    if isinstance(payload.get("items"), list):
        return [p for p in payload["items"] if isinstance(p, dict)]

    return []


def fetch_posts_via_rapidapi(
    *,
    request_url: str,
    api_key: str,
    api_host: Optional[str] = None,
    subreddits: List[str],
    keywords: List[str],
    max_total_hits: int = 50,
    max_age_days: int = 2,
    timeout_s: int = 30,
    per_request_sleep_s: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Fetch posts via RapidAPI (no official Reddit API).

    Notes:
    - RapidAPI almost always requires `X-RapidAPI-Key`.
    - Many endpoints also require `X-RapidAPI-Host` (the API host on RapidAPI).
      If not provided, we try to infer it from the request URL hostname.
    - `request_url` can include placeholders:
        - {subreddit} will be replaced for each subreddit.
    """
    if not request_url or not api_key:
        return []

    inferred_host = urlparse(request_url).netloc
    host = api_host or inferred_host or None

    headers = {"X-RapidAPI-Key": api_key}
    if host:
        headers["X-RapidAPI-Host"] = host

    key_lower = [k.lower() for k in keywords] if keywords else []
    now_utc = datetime.now(timezone.utc)
    min_dt = now_utc - timedelta(days=max_age_days)

    posts: List[Dict[str, Any]] = []
    total_hits = 0

    session = requests.Session()

    for sub in subreddits:
        if total_hits >= max_total_hits:
            break

        url = request_url.format(subreddit=sub)
        try:
            if per_request_sleep_s and per_request_sleep_s > 0:
                time.sleep(per_request_sleep_s)

            resp = session.get(url, headers=headers, timeout=timeout_s)
            if resp.status_code == 429:
                print("   ⏳ RapidAPI 触发 429（配额/频率限制），请稍后重试或检查套餐。")
                time.sleep(2.0)
                continue
            if resp.status_code == 402:
                # RapidAPI often uses 402 for plan/quota issues
                print("   💳 RapidAPI 返回 402：可能套餐/配额不足（MONTHLY quota exceeded）。")
                continue
            if resp.status_code in {401, 403}:
                print(
                    f"   🔐 RapidAPI 鉴权失败 ({resp.status_code}) r/{sub}：请检查 api_key/api_host 是否正确。"
                )
                continue
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            print(f"   ⚠️ RapidAPI 请求失败 r/{sub}: {e}")
            continue

        items = _extract_listing_items(payload)
        if not items:
            print(f"   ⚠️ RapidAPI 返回为空 r/{sub}（响应结构可能不匹配或该版块无数据）。")
        for item in items:
            if total_hits >= max_total_hits:
                break

            normalized = _normalize_post(item, fallback_subreddit=sub)
            if not normalized:
                continue

            title = normalized.get("title") or ""
            if key_lower and not any(k in title.lower() for k in key_lower):
                continue

            created_ts = float(normalized.get("created_utc") or 0.0)
            if created_ts > 0:
                created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
                if created_dt < min_dt:
                    continue

            posts.append(normalized)
            total_hits += 1

    return posts


def load_rapidapi_config(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Settings precedence: ENV > settings.yaml
    """
    rapid_cfg = (settings or {}).get("rapidapi", {}) if isinstance(settings, dict) else {}

    # Prefer dedicated env vars for reddit patrol so it won't interfere with other RapidAPI usage.
    dedicated_key = os.getenv("REDDIT_PATROL_RAPIDAPI_KEY") or ""
    key_fallback = os.getenv("RAPIDAPI_KEY") or os.getenv("X_RAPIDAPI_KEY") or ""

    enabled_raw = os.getenv(
        "REDDIT_PATROL_RAPIDAPI_ENABLED", os.getenv("RAPIDAPI_ENABLED", str(rapid_cfg.get("enabled", "true")))
    )
    enabled = str(enabled_raw).lower() in {"1", "true", "yes", "y", "on"}

    request_url = os.getenv(
        "REDDIT_PATROL_RAPIDAPI_REQUEST_URL", os.getenv("RAPIDAPI_REQUEST_URL", rapid_cfg.get("request_url", ""))
    )
    api_host = os.getenv(
        "REDDIT_PATROL_RAPIDAPI_HOST", os.getenv("RAPIDAPI_HOST", rapid_cfg.get("api_host", "")) or ""
    )
    timeout_s_raw = os.getenv(
        "REDDIT_PATROL_RAPIDAPI_TIMEOUT_S", os.getenv("RAPIDAPI_TIMEOUT_S", str(rapid_cfg.get("timeout_s", 30)))
    )

    return {
        "enabled": enabled,
        "request_url": request_url,
        "api_key": dedicated_key or key_fallback or rapid_cfg.get("api_key", ""),
        "api_host": api_host or None,
        "timeout_s": int(timeout_s_raw),
    }

