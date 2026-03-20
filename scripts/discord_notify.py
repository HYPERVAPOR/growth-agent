"""
Workflow D 推送脚本：主频道 + Thread 格式
用法：uv run python3 discord_notify.py <social_json> <blog_json> <channel>
"""
import sys, json, subprocess, time
from pathlib import Path

social_json, blog_json, channel = sys.argv[1], sys.argv[2], sys.argv[3]

def send(msg, target=None):
    cmd = ["openclaw", "message", "send", "--channel", "discord",
           "--target", target or channel, "--message", msg, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return str(data.get("payload", {}).get("result", {}).get("messageId") or "")
    except Exception:
        print(f"send err: {result.stderr}")
        return None

def create_thread(msg_id, name):
    cmd = ["openclaw", "message", "thread", "create", "--channel", "discord",
           "--target", channel, "--message-id", msg_id, "--thread-name", name[:100], "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return str(data.get("payload", {}).get("thread", {}).get("id") or "")
    except Exception:
        print(f"thread create err: {result.stderr}")
        return None

def thread_reply(thread_id, msg):
    cmd = ["openclaw", "message", "thread", "reply", "--channel", "discord",
           "--target", thread_id, "--message", msg]
    subprocess.run(cmd, capture_output=True, text=True)

def truncate(text, limit=500):
    v = " ".join((text or "").split())
    return v if len(v) <= limit else v[:limit-3] + "..."

# ── X 监听 ──────────────────────────────────────────────────
social_data = json.loads(Path(social_json).read_text())
date_str = Path(social_json).stem.split("_")[-2]
date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

send(f"📡 X 社媒监听 · {date_fmt}\n高价值机会: {len(social_data)} 条")
time.sleep(1)

for i, opp in enumerate(social_data, start=1):
    source = opp.get("source_content") or {}
    author = source.get("author") or "Unknown"
    score = opp.get("score", 0)
    reason = opp.get("reason") or "N/A"
    tweet = opp.get("suggested_tweet") or "N/A"
    link = source.get("link", "N/A")
    pub_date = source.get("pub_date") or "N/A"
    summary = truncate(source.get("content") or "")

    main_msg = (
        f"[{score}/10] #{i} {author}\n"
        f"匹配原因: {reason}\n\n"
        f"原创推文（可直接发布）:\n{tweet}\n\n"
        f"操作: 回复 'x{i}' 重生成社媒图"
    )
    msg_id = send(main_msg)
    print(f"X #{i} msg_id={msg_id}")
    time.sleep(1)

    if msg_id:
        thread_id = create_thread(msg_id, f"#{i} {author} 详情")
        print(f"  thread_id={thread_id}")
        if thread_id:
            content = f"原文链接: {link}\n发布时间: {pub_date}"
            summary_zh = source.get("summary_zh") or summary
            if summary_zh:
                content += f"\n\n原文摘要:\n{summary_zh}"
            thread_reply(thread_id, content)
    time.sleep(1)

# ── 博客选题 ──────────────────────────────────────────────────
blog_data = json.loads(Path(blog_json).read_text())
send(f"📝 博客选题 · {date_fmt}\n高价值选题: {len(blog_data)} 条")
time.sleep(1)

for i, opp in enumerate(blog_data, start=1):
    source = opp.get("source_content") or {}
    title = opp.get("suggested_title") or "Untitled"
    score = opp.get("score", 0)
    reason = opp.get("reason") or "N/A"
    keyword = opp.get("target_keyword") or "N/A"
    intent = opp.get("search_intent") or "N/A"
    angle = opp.get("blog_angle") or "N/A"
    link = source.get("link", "N/A")
    pub_date = source.get("pub_date") or "N/A"
    source_name = source.get("source") or source.get("author") or "Unknown"
    source_author = source.get("author") or source_name
    secondary = ", ".join(opp.get("secondary_keywords") or [])
    outline = opp.get("outline") or []
    summary = truncate(source.get("content") or "")

    main_msg = (
        f"[{score}/10] #{i} {title}\n"
        f"目标关键词: {keyword}\n"
        f"搜索意图: {intent}\n\n"
        f"为什么值得写: {reason}\n\n"
        f"操作: 回复 'b{i}' 生成博客封面"
    )
    msg_id = send(main_msg)
    print(f"Blog #{i} msg_id={msg_id}")
    time.sleep(1)

    if msg_id:
        thread_id = create_thread(msg_id, f"#{i} {title[:40]} 详情")
        print(f"  thread_id={thread_id}")
        if thread_id:
            content = (
                f"写作角度: {angle}\n"
                f"来源: {source_author} / {source_name}\n"
                f"原文链接: {link}\n"
                f"发布时间: {pub_date}"
            )
            if secondary:
                content += f"\n次关键词: {secondary}"
            if outline:
                content += "\n\n建议结构:\n" + "\n".join(f"- {s}" for s in outline)
            summary_zh = source.get("summary_zh") or summary
            if summary_zh:
                content += f"\n\n原文摘要:\n{summary_zh}"
            thread_reply(thread_id, content)
    time.sleep(1)

print("推送完成")
