from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright


def fetch_posts_via_playwright(
    ws_url: str,
    subreddits: List[str],
    keywords: List[str],
    max_total_hits: int = 50,
    max_age_days: int = 2,
) -> List[Dict[str, Any]]:
    """通过 AdsPower + Playwright 从浏览器中抓取 Reddit 帖子。

    返回的每条帖子结构与 HTTP 版抓取保持一致，便于后续 AI 打分与入库。
    """
    if not ws_url:
        print("⚠️ 未获取到 AdsPower 浏览器 ws_url，无法通过浏览器抓取。")
        return []

    posts: List[Dict[str, Any]] = []
    key_lower = [k.lower() for k in keywords] if keywords else []
    now_utc = datetime.now(timezone.utc)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        total_hits = 0

        for sub in subreddits:
            if total_hits >= max_total_hits:
                print(f"\n🏁 已达全局目标上限 ({max_total_hits} 个)，停止巡检。")
                break

            print(f"\n🔍 正在巡检: r/{sub}...")
            try:
                page.goto(
                    f"https://www.reddit.com/r/{sub}/new/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                # 简单等待一会儿，确保帖子元素加载完成
                page.wait_for_timeout(5000)
                shreddit_posts = page.locator("shreddit-post").all()
            except Exception as e:
                print(f"   ⚠️ 无法访问版块 r/{sub}: {e}")
                continue

            for post in shreddit_posts[:15]:
                if total_hits >= max_total_hits:
                    print("   🔔 已达全局上限，跳出当前版块")
                    break

                pid = post.get_attribute("id")
                title = post.get_attribute("post-title") or ""
                if not pid or not title:
                    continue

                # 关键词筛选
                if key_lower and not any(k in title.lower() for k in key_lower):
                    continue

                raw_time = post.get_attribute("created-timestamp") or ""
                try:
                    post_dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                    time_diff = now_utc - post_dt
                    if time_diff > timedelta(days=max_age_days):
                        print("   ⏭️ 帖子超过时间窗口，跳过")
                        continue
                except Exception:
                    continue

                permalink = post.get_attribute("permalink") or ""
                reddit_url = f"https://www.reddit.com{permalink}" if permalink else ""
                score = post.get_attribute("score") or "0"
                c_count = post.get_attribute("comment-count") or "0"

                posts.append(
                    {
                        "post_id": pid,
                        "title": title,
                        "url": reddit_url,
                        "subreddit": sub,
                        "upvotes": score,
                        "comments_count": c_count,
                        "created_utc": post_dt.replace(tzinfo=timezone.utc).timestamp(),
                    }
                )
                total_hits += 1
                print(
                    f"   ✨ 发现候选 [{total_hits}/{max_total_hits}]: "
                    f"{title[:40]}... | 👍 {score} | 💬 {c_count}"
                )

        browser.close()

    return posts

