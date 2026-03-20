#!/usr/bin/env bash
# Workflow D: Social Listener
# 跑完后写 flag，由 OpenClaw heartbeat 检测并用 message tool 推送到 Discord

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FLAG_FILE="$PROJECT_ROOT/data/social_listener/.pending_notify"

cd "$PROJECT_ROOT"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Workflow D..."
uv run python -m growth_agent.main run workflow-d

# 找最新报告
SOCIAL_JSON=$(ls -t "$PROJECT_ROOT/data/social_listener/reports"/puppyone_opportunities_*.json 2>/dev/null | head -1)
BLOG_JSON=$(ls -t "$PROJECT_ROOT/data/social_listener/reports"/puppyone_blog_materials_*.json 2>/dev/null | head -1)

if [ -z "$SOCIAL_JSON" ] || [ -z "$BLOG_JSON" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: 报告文件未找到"
    exit 1
fi

# 写 flag，内容为报告路径，由 heartbeat 读取后推送
cat > "$FLAG_FILE" << FLAGEOF
social_json=$SOCIAL_JSON
blog_json=$BLOG_JSON
channel=channel:1481163930759073953
FLAGEOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Workflow D done. Flag written: $FLAG_FILE"
