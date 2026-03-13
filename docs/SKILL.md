---
name: reddit-patrol
description: Reddit 社区巡检与互动系统。负责监控指定版块、筛选高价值帖子、根据人设生成评论，并追踪发布状态。当员工说"开始巡检"、"查询 Reddit 动态"、"巡检科技板块"、"标记已发布"时触发。
---

# Reddit 巡检系统 (Reddit Patrol)

## 🔓 核心规则

1. **状态唯一性**：任何帖子在评论生成后默认为 `pending` 状态。一旦标记为 `published`，系统在后续巡检中必须彻底跳过，不得再次展示。
2. **文本风格规范**（严格执行）：
   * **Everyday 模式**：禁止使用破折号和分号。禁止使用祈使句。保持自然的口语节奏。
   * **内容红线**：严禁提及初创公司名称。严禁提及具体 AI 产品名（Notion、NotebookLM、Cursor 等公认工具除外）。

## ⏰ 时间规范

**所有操作记录必须使用 UTC+8（北京时间）。**

获取当前 UTC+8 时间戳：
```bash
TZ=Asia/Shanghai date "+%Y-%m-%dT%H:%M:%S+08:00"

📂 目录结构

reddit_patrol/
  config/
    keywords/          # 关键词列表 (everyday.csv, tech.csv)
    prompts/           # AI 指令 (classifier_*.json, generator_*.json)
    subreddits/        # 目标版块 (everyday.csv, tech.csv)
    settings.yaml      # API 与运行配置
  data/
    processed_posts.json  # 核心数据库：存储帖子信息与发布状态

📊 数据格式 (processed_posts.json)
processed_posts.json 是一个 JSON 数组，记录格式如下：

JSON
{
    "post_id": "19abcde",
    "title": "How to use LLMs for research?",
    "url": "[https://reddit.com/r/short_url](https://reddit.com/r/short_url)",
    "mode": "tech",
    "score": 8.5,
    "generated_comment": "Interesting perspective on using retrieval-augmented generation...",
    "status": "pending",
    "timestamp": "2026-03-13T15:30:00+08:00"
}