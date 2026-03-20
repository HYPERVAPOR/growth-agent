import json
import os
import random
import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import requests
import yaml

from .core.ai_handler import AIHandler
from .core.db_manager import DBManager
from .core.rapidapi_scraper import fetch_posts_via_rapidapi, load_rapidapi_config


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


def _score_one_with_ai(
    ai_client: Any, classifier_prompt: Dict[str, Any], post: Dict[str, Any]
) -> Dict[str, Any] | None:
    """对单条帖子进行 AI 评分，返回带 ai_* 字段的 post（不满足则返回 None）。"""
    if isinstance(ai_client, Placeholder):
        return post

    now_utc = datetime.now(timezone.utc)
    now_cn = now_utc + timedelta(hours=8)

    created_ts = post.get("created_utc") or 0
    try:
        post_time = datetime.fromtimestamp(float(created_ts), tz=timezone.utc) + timedelta(
            hours=8
        )
    except Exception:
        post_time = now_cn

    payload = {
        "title": post.get("title"),
        "upvotes": post.get("upvotes", 0),
        "comments_count": post.get("comments_count", 0),
        "post_time": post_time.isoformat(),
        "current_time": now_cn.isoformat(),
    }
    res = ai_client.call(system_rules=classifier_prompt, user_data=payload)
    if not res:
        return None

    tag = res.get("tag", "no")
    score = res.get("ai_score", 0)
    if tag in {"yes", "maybe"} and score >= 25:
        post["ai_tag"] = tag
        post["ai_score"] = score
        post["ai_reason"] = res.get("reasoning", "")
        return post
    return None


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
ai = _init_ai()


def run_patrol():
    """执行巡检任务的逻辑"""
    print("\n🚀 开始 Reddit 巡检...")
    settings = _load_settings()
    mode = (
        os.getenv("REDDIT_PATROL_MODE")
        or (input("请输入巡检模式 (tech/everyday): ").strip() if sys.stdin.isatty() else "")
        or settings.get("defaults", {}).get("mode", "tech")
        or "tech"
    )
    # 评估预算：最多评估多少条帖子（与“要新增几条”解耦）
    # 说明：用户说“要 1 条”只影响 target_new，不应该把评估预算也限制成 1。
    eval_budget = int(os.getenv("REDDIT_PATROL_EVAL_BUDGET") or 50)
    max_age_days = int(
        os.getenv("REDDIT_PATROL_MAX_AGE_DAYS")
        or settings.get("defaults", {}).get("max_age_days", 2)
        or 2
    )
    # 本轮目标新增条数：由 OpenClaw 对话理解后注入环境变量（不写入 settings.yaml）
    # 0 表示不限制，但为了效率建议总是设置一个正整数。
    target_new = int(os.getenv("REDDIT_PATROL_TARGET_NEW") or 0)

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

    # 流式巡检：逐个 subreddit 拉取，逐条评分；满足 target_new 后立刻停止继续抓取
    try:
        rapid_cfg = load_rapidapi_config(settings)
        if not (
            rapid_cfg.get("enabled")
            and rapid_cfg.get("request_url")
            and rapid_cfg.get("api_key")
        ):
            print("☹️ RapidAPI 未配置或未启用：请检查 settings.yaml 的 rapidapi.* 配置。")
            return
    except Exception as e:
        print(f"⚠️ RapidAPI 配置读取失败: {e}")
        return

    print("🌐 使用 RapidAPI 抓取帖子（逐条评分，命中即停）。")

    fetched_total = 0
    new_count = 0

    # 每个 subreddit 最多取多少条用于逐条评估（避免一次抓太多）
    per_sub_limit = int(os.getenv("REDDIT_PATROL_PER_SUB_LIMIT") or 10)
    if per_sub_limit <= 0:
        per_sub_limit = 25
    per_sub_limit = min(50, per_sub_limit)

    for sub in subreddits:
        if target_new > 0 and new_count >= target_new:
            break
        if fetched_total >= eval_budget:
            break

        # 对单个 subreddit 请求一次，拿到一页 posts（随后逐条处理）
        remaining = eval_budget - fetched_total
        take = min(per_sub_limit, remaining)
        posts = fetch_posts_via_rapidapi(
            request_url=rapid_cfg["request_url"],
            api_key=rapid_cfg["api_key"],
            api_host=rapid_cfg.get("api_host"),
            timeout_s=int(rapid_cfg.get("timeout_s") or 30),
            subreddits=[sub],
            keywords=[],
            max_total_hits=take,
            max_age_days=max_age_days,
        )
        if not posts:
            continue

        for p in posts:
            if target_new > 0 and new_count >= target_new:
                break
            if fetched_total >= eval_budget:
                break

            fetched_total += 1

            # 关键词过滤（若 keywords 为空则不触发）
            if keywords:
                title_lower = (p.get("title") or "").lower()
                if not any(k.lower() in title_lower for k in keywords):
                    continue

            scored_post = _score_one_with_ai(ai_client, prompts["classifier"], p)
            if not scored_post:
                continue

            score = scored_post.get("ai_score", 0)
            generated_comment = _generate_comment(
                ai_client, prompts["generator"], scored_post
            )

            post_record = {
                "post_id": scored_post["post_id"],
                "title": scored_post["title"],
                "url": scored_post["url"],
                "mode": mode,
                "score": float(score),
                "generated_comment": generated_comment,
            }

            if db.add_post(post_record):
                new_count += 1
                print(
                    f"✅ 新增高价值帖子：[{scored_post.get('subreddit')}] "
                    f"{scored_post.get('title')} (score={score})"
                )
            else:
                print(f"↩️ 已存在，跳过：[{scored_post.get('subreddit')}] {scored_post.get('title')}")

    if fetched_total == 0:
        print("☹️ RapidAPI 未返回帖子，请检查配额/鉴权/endpoint 是否可用。")
        return

    if new_count == 0:
        print(f"☹️ 本轮未新增高价值帖子（已评估 {fetched_total} 条）。")
    else:
        if target_new > 0:
            print(
                f"🎉 本轮巡检完成：评估 {fetched_total} 条，新增 {new_count}/{target_new} 条。"
            )
        else:
            print(f"🎉 本轮巡检完成：评估 {fetched_total} 条，新增 {new_count} 条。")


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
    """
    交互式：显示菜单（适合本地终端手动跑）
    非交互式（OpenClaw/CI）：默认直接跑一次巡检并退出

    CLI:
      - patrol: python3 scripts/reddit_patrol.py patrol --mode tech
      - list:   python3 scripts/reddit_patrol.py list
    """
    parser = argparse.ArgumentParser(prog="reddit-patrol", add_help=True)
    sub = parser.add_subparsers(dest="cmd")

    p_patrol = sub.add_parser("patrol", help="run patrol once")
    p_patrol.add_argument(
        "--mode",
        choices=["tech", "everyday"],
        default=None,
        help="patrol mode (overrides defaults.mode)",
    )

    sub.add_parser("list", help="list pending and mark published (interactive)")

    args, _unknown = parser.parse_known_args()

    if args.cmd == "patrol":
        if args.mode:
            os.environ["REDDIT_PATROL_MODE"] = args.mode
        run_patrol()
        return
    if args.cmd == "list":
        list_and_mark()
        return

    # 没有显式命令：在非交互场景下默认跑一次巡检
    if not sys.stdin.isatty():
        run_patrol()
        return

    # 交互菜单
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

