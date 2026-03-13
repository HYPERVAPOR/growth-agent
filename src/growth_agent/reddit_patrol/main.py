import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import requests
import yaml

from .core.ai_handler import AIHandler
from .core.browser_engine import BrowserEngine
from .core.db_manager import DBManager
from .core.scraper import fetch_posts_via_playwright


class Placeholder:
    def __getattr__(self, name):
        return lambda *args, **kwargs: print(
            f"提示：{name} 功能还在开发中，请先编写对应的 py 文件"
        )


def _load_settings() -> Dict[str, Any]:
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "config", "settings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _init_browser() -> Any:
    """从 config/settings.yaml 加载 AdsPower 配置并初始化浏览器引擎。"""
    try:
        cfg = _load_settings()
        ads_cfg = cfg.get("adspower", {})
        api_key = ads_cfg.get("api_key")
        base_url = ads_cfg.get("base_url", "http://127.0.0.1:50325")
        user_id = ads_cfg.get("default_user_id")

        if not (api_key and user_id):
            print("⚠️ AdsPower 配置不完整，使用占位浏览器。")
            return Placeholder()

        return BrowserEngine(api_key=api_key, base_url=base_url, user_id=user_id)
    except Exception as e:
        print(f"⚠️ 无法加载 AdsPower 配置: {e}")
        return Placeholder()


def _init_ai() -> Any:
    """从 config/settings.yaml 加载 OpenRouter 配置并初始化 AIHandler。"""
    try:
        cfg = _load_settings()
        ai_cfg = cfg.get("openrouter", {})
        api_key = ai_cfg.get("api_key")
        model = ai_cfg.get("model")
        api_url = ai_cfg.get("api_url", "https://openrouter.ai/api/v1/chat/completions")

        if not (api_key and model):
            print("⚠️ OpenRouter 配置不完整，使用占位 AI。")
            return Placeholder()

        return AIHandler(api_key=api_key, api_url=api_url, model=model)
    except Exception as e:
        print(f"⚠️ 无法加载 OpenRouter 配置: {e}")
        return Placeholder()


def _load_csv_column(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    values: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    if not lines:
        return []
    # 跳过表头
    for line in lines[1:]:
        if line:
            values.append(line)
    return values


def _load_prompts(mode: str) -> Dict[str, Any]:
    base_dir = os.path.join(os.path.dirname(__file__), "config", "prompts")
    classifier_file = f"classifier_{mode}.json"
    generator_file = f"generator_{mode}.json"
    with open(os.path.join(base_dir, classifier_file), "r", encoding="utf-8") as f:
        classifier = json.load(f)
    with open(os.path.join(base_dir, generator_file), "r", encoding="utf-8") as f:
        generator = json.load(f)
    return {"classifier": classifier, "generator": generator}


def _filter_by_keywords(
    posts: List[Dict[str, Any]], keywords: List[str]
) -> List[Dict[str, Any]]:
    if not keywords:
        return posts
    key_lower = [k.lower() for k in keywords]
    filtered: List[Dict[str, Any]] = []
    for p in posts:
        title = (p.get("title") or "").lower()
        if any(k in title for k in key_lower):
            filtered.append(p)
    return filtered


def _score_with_ai(
    ai_client: Any, classifier_prompt: Dict[str, Any], posts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """用分类器 prompt 给帖子打分，返回 tag 为 yes/maybe 且分数较高的帖子。"""
    if isinstance(ai_client, Placeholder):
        return posts

    now_utc = datetime.now(timezone.utc)
    # 转为北京时间
    now_cn = now_utc + timedelta(hours=8)

    selected: List[Dict[str, Any]] = []
    for p in posts:
        created_ts = p.get("created_utc") or 0
        post_time = datetime.fromtimestamp(created_ts, tz=timezone.utc) + timedelta(
            hours=8
        )
        payload = {
            "title": p.get("title"),
            "upvotes": p.get("upvotes", 0),
            "comments_count": p.get("comments_count", 0),
            "post_time": post_time.isoformat(),
            "current_time": now_cn.isoformat(),
        }
        res = ai_client.call(system_rules=classifier_prompt, user_data=payload)
        if not res:
            continue
        tag = res.get("tag", "no")
        score = res.get("ai_score", 0)
        if tag in {"yes", "maybe"} and score >= 25:
            p["ai_tag"] = tag
            p["ai_score"] = score
            p["ai_reason"] = res.get("reasoning", "")
            selected.append(p)
    return selected


def _generate_comment(
    ai_client: Any, generator_prompt: Dict[str, Any], post: Dict[str, Any]
) -> str:
    if isinstance(ai_client, Placeholder):
        return "这条评论是占位内容，你可以在接入 AI 后自动生成更自然的回复。"
    payload = {
        "op_post_excerpt": (post.get("title") or "")[:240],
        "target_subreddit": post.get("subreddit"),
        "comment_intent": "reply with a thoughtful, context-aware comment",
    }
    res = ai_client.call(system_rules=generator_prompt, user_data=payload)
    if not res:
        return "暂时无法生成评论，但这条帖子已被标记为高价值，可以手动补充评论。"
    return (
        res.get("comment")
        or res.get("generated_comment")
        or "生成内容为空，请稍后重试。"
    )


# 初始化账本与服务
db = DBManager()
browser = _init_browser()
ai = _init_ai()


def run_patrol():
    """执行巡检任务的逻辑"""
    print("\n🚀 开始 Reddit 巡检...")
    mode = input("请输入巡检模式 (tech/everyday): ").strip() or "tech"

    # 尝试启动 AdsPower 浏览器环境
    ws_url = None
    try:
        ws_url = browser.get_ws_url()
        if ws_url:
            print("✅ 已请求 AdsPower 打开浏览器环境。")
        else:
            print(
                "⚠️ AdsPower 启动失败，请检查本地 AdsPower 是否已打开，并确认 config/settings.yaml 配置正确。"
            )
    except Exception as e:
        print(f"⚠️ 调用 AdsPower 失败: {e}")
        ws_url = None

    mode = "tech" if mode.lower().startswith("t") else "everyday"

    # 加载配置与 prompt
    base_dir = os.path.dirname(__file__)
    keywords_path = os.path.join(base_dir, "config", "keywords", f"{mode}.csv")
    subs_path = os.path.join(base_dir, "config", "subreddits", f"{mode}.csv")

    keywords = _load_csv_column(keywords_path)
    subreddits = _load_csv_column(subs_path)
    if subreddits:
        random.shuffle(subreddits)
    prompts = _load_prompts(mode)

    print(f"📡 巡检模式: {mode}")
    print(f"📌 目标版块: {', '.join(subreddits) if subreddits else '（未配置）'}")

    ai_client = ai

    if not ws_url:
        print("☹️ 未能成功启动 AdsPower 浏览器环境，本轮巡检终止。")
        return

    # 通过浏览器抓取最新帖子
    raw_posts = fetch_posts_via_playwright(
        ws_url=ws_url,
        subreddits=subreddits,
        keywords=keywords,
        max_total_hits=50,
        max_age_days=2,
    )
    if not raw_posts:
        print("☹️ 未从 Reddit 抓到任何帖子，请稍后重试。")
        return

    print(f"🔎 共抓取 {len(raw_posts)} 条帖子，按关键词初筛中...")
    filtered = _filter_by_keywords(raw_posts, keywords)
    print(f"✅ 关键词筛选后剩余 {len(filtered)} 条。正在使用 AI 评分...")

    # 用 AI 打分筛选高价值帖子
    scored = _score_with_ai(ai_client, prompts["classifier"], filtered)
    print(f"✨ AI 评估后保留 {len(scored)} 条候选帖子。")

    if not scored:
        print("☹️ 本轮没有高价值帖子。")
        return

    # 逐条生成评论并写入数据库
    new_count = 0
    for p in scored:
        post_id = p["post_id"]
        title = p["title"]
        url = p["url"]
        subreddit = p["subreddit"]
        score = p.get("ai_score", 0)

        generated_comment = _generate_comment(ai_client, prompts["generator"], p)

        post_record = {
            "post_id": post_id,
            "title": title,
            "url": url,
            "mode": mode,
            "score": float(score),
            "generated_comment": generated_comment,
        }

        if db.add_post(post_record):
            new_count += 1
            print(f"✅ 新增高价值帖子：[{subreddit}] {title} (score={score})")
        else:
            print(f"↩️ 已存在，跳过：[{subreddit}] {title}")

    if new_count == 0:
        print("☹️ 本轮没有新增高价值帖子（可能都已在账本中）。")
    else:
        print(f"🎉 本轮巡检完成，共新增 {new_count} 条高价值帖子，已存入待发布清单。")


def list_and_mark():
    """展示清单并根据编号标记已发布"""
    pending = db.get_pending_posts()

    if not pending:
        print("\n当前没有待发布的帖子。")
        return

    print("\n📋 待发布清单：")
    for i, post in enumerate(pending, 1):
        print(f"{i}. 【{post['title']}】")
        print(f"   建议评论：{post['generated_comment']}")
        print(f"   (ID: {post['post_id']})")
        print("-" * 30)

    user_choice = input("\n请输入已发布的编号（直接回车取消）: ").strip()

    if not user_choice:
        return

    try:
        index = int(user_choice) - 1
        if 0 <= index < len(pending):
            target_id = pending[index]["post_id"]
            if db.mark_as_published(target_id):
                print(f"✅ 成功！已将第 {user_choice} 条标记为已发布。")
        else:
            print("⚠️ 编号超出了范围。")
    except ValueError:
        print("⚠️ 请输入有效的数字编号。")


def main():
    while True:
        print("\n=== Reddit Patrol 控制台 ===")
        print("1. 执行巡检 (Patrol)")
        print("2. 查看待发布并标记 (Mark Published)")
        print("q. 退出")

        choice = input("\n请选择操作: ").strip().lower()

        if choice == "1":
            run_patrol()
        elif choice == "2":
            list_and_mark()
        elif choice == "q":
            print("再见！")
            break
        else:
            print("无效输入，请重新选择。")

