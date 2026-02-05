# Growth Agent - AI Agent System Prompt

> **puppyone ai 工作区指导手册**
> **定位**: AI 智能体最强上下文库 (The #1 context base for AI agents)
> **网址**: https://www.puppyone.ai/en

**项目职责**: 项目位于 `/growth-agent`，负责 puppyone ai 的研发协作、内容创作与品牌运营。

---

## 核心架构

```
Growth Agent = File-system DB + 3 Workflows + LLM Processing
```

**技术栈**:
- **存储**: JSONL (文件系统数据库，每行一个 JSON)
- **调度**: APScheduler (定时任务，默认每天 8:00 AM Beijing)
- **LLM**: OpenRouter API (Gemini)
- **向量**: LanceDB (可选，用于语义搜索)

**数据流**:
```
Ingestion → Curation → Generation
   ↓            ↓            ↓
inbox/    curated/    blogs/
```

---

## 核心工作流与执行命令

### 🔄 Workflow B: 内容创作与品牌运营 (核心)

**职责**: 从 X/Twitter 和 RSS 收集情报 → AI 筛选 → 生成官方 Blog

#### 完整流程（一键执行）
```bash
uv run python -m growth_agent.main run workflow-b
```

#### 分步执行（调试/手动控制）
```bash
# 阶段 1: 获取内容 (Ingestion)
uv run python scripts/sync_content.py
# → 从 X Creators 获取 20 条推文
# → 从 RSS Feeds 获取 20 篇文章
# → 存储到 data/inbox/items.jsonl

# 阶段 2: AI 筛选 (Curation)
uv run python scripts/curate_content.py
# → LLM 评分每个 item (0-100)
# → 过滤低分内容 (score < 60)
# → 选择 Top-10 高质量内容
# → 存储到 data/curated/{YYYY-MM-DD}_ranked.jsonl

# 阶段 3: 生成博客 (Generation)
uv run python scripts/generate_blog.py
# → 读取当天的 curated 文件
# → LLM 生成博客文章（带 YAML frontmatter）
# → 保存到 data/blogs/{ID}_{slug}.md
```

**配置订阅源**:
```bash
# 编辑 X/Twitter 订阅
vim data/subscriptions/x_creators.jsonl
# {"id": "1689650211810123776", "username": "puppyone_ai", "followers_count": 1000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}

# 编辑 RSS 订阅
vim data/subscriptions/rss_feeds.jsonl
# {"id": "techcrunch", "url": "https://techcrunch.com/feed/", "title": "TechCrunch", "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

---

### 🐙 Workflow A: 研发协作与质量管理

**职责**: GitHub Issues 全生命周期管理、Bug 追踪

```bash
# 手动触发
uv run python scripts/sync_github_issues.py
```

**功能**:
- 使用 `gh issue list` 获取 issues
- Upsert 逻辑（基于 `updated_at` 时间戳）
- 存储到 `data/github/issues.jsonl` (覆盖模式)

---

### 📊 Workflow C: 社交媒体影响力监测

**职责**: 收集 X（已实现）/LinkedIn（待实现） 互动数据，优化运营策略

```bash
# 使用默认账号 (@puppyone_ai)
uv run python scripts/sync_metrics.py

# 指定账号
uv run python scripts/sync_metrics.py username user_id
```

**功能**:
- 获取最新 20 条推文
- 提取互动指标 (likes, retweets, replies)
- 计算总互动数：`engagements = replies + retweets + likes + quotes`
- 存储到 `data/metrics/stats.jsonl` (覆盖模式)

---

## 数据模型速查

### InboxItem (原始内容)
**位置**: `data/inbox/items.jsonl`
```json
{
  "id": "unique-id-123",
  "source": "x",  // "x" 或 "rss"
  "content_type": "post",  // "post" 或 "article"
  "url": "https://x.com/user/status/123",
  "content": "完整文本内容...",
  "author_name": "Author Name",
  "published_at": "2026-02-05T10:00:00Z"
}
```

### CuratedItem (AI 精选)
**位置**: `data/curated/{YYYY-MM-DD}_ranked.jsonl`
```json
{
  "score": 85,  // LLM 评分 (0-100)
  "summary": "内容摘要...",
  "comment": "AI 评价...",
  "rank": 1,  // 当天排名
  // ...继承 InboxItem 字段
}
```

### BlogPost (生成博客)
**位置**: `data/blogs/{ID}_{slug}.md`
```markdown
---
title: Blog Title
date: 2026-02-05T10:00:00Z
summary: Brief summary (50-300 chars)
tags: [AI, Technology]
author: Growth Agent
---

# Introduction

Content here...
```

### GitHubIssue (问题追踪)
**位置**: `data/github/issues.jsonl`
```json
{
  "id": 123,
  "title": "Issue title",
  "state": "open",  // "open" 或 "closed"
  "updated_at": "2026-02-05T12:00:00Z"
}
```

### MetricStat (互动指标)
**位置**: `data/metrics/stats.jsonl`
```json
{
  "platform": "x",
  "content_id": "1234567890",
  "engagements": 150,  // replies + retweets + likes + quotes
  "likes": 100,
  "retweets": 40,
  "replies": 10
}
```

---

## 常用命令速查

### 初始化与配置
```bash
# 初始化数据目录
uv run python -m growth_agent.main init

# 同步依赖
uv sync

# 配置环境变量
vim .env  # X_RAPIDAPI_KEY, OPENROUTER_API_KEY
```

### 定时任务（生产环境）
```bash
# 启动调度器（前台运行）
uv run python -m growth_agent.main schedule

# 配置 systemd 服务（后台运行）
sudo cp growth-agent.service.example /etc/systemd/system/growth-agent.service
# 编辑 User 和 WorkingDirectory
sudo systemctl enable growth-agent
sudo systemctl start growth-agent
sudo journalctl -u growth-agent -f  # 查看日志
```

### 数据查询
```bash
# 统计 inbox 内容数量
cat data/inbox/items.jsonl | jq '. | length'

# 查看高分精选内容
cat data/curated/2026-02-05_ranked.jsonl | jq '.[] | select(.score > 80)'

# 查看最新博客
ls -lt data/blogs/*.md | head -1 | xargs cat

# 查看互动指标
cat data/metrics/stats.jsonl | jq '.[] | {url, engagements}'
```

### 日志与调试
```bash
# 查看当天日志
tail -f data/logs/$(date +%Y-%m-%d).log

# 搜索错误
grep -i "error\|failed" data/logs/*.log

# 验证 API 连接
uv run python -c "
from growth_agent.config import reload_settings
from growth_agent.ingestors.x_twitter import XTwitterIngestor
settings = reload_settings()
ingestor = XTwitterIngestor(settings)
tweets = ingestor.fetch_creator_tweets('1689650211810123776', 'puppyone_ai', count=1)
print(f'Fetched {len(tweets)} tweets')
"
```

---

## 环境配置

### 必需配置 (.env)
```bash
# X/Twitter API
X_RAPIDAPI_KEY=your_key_here
X_RAPIDAPI_HOST=twitter241.p.rapidapi.com

# LLM API
OPENROUTER_API_KEY=sk-...

# 定时任务
INGESTION_SCHEDULE=0 8 * * *  # 每天 8:00 AM Beijing
SCHEDULER_TIMEZONE=Asia/Shanghai

# Workflow B 配置
CURATION_MIN_SCORE=60  # 筛选阈值
CURATION_TOP_K=10      # 选择 Top-K
BLOG_GENERATION_ENABLED=true
```

### 可选配置
```bash
# GitHub (Workflow A)
GITHUB_TOKEN=your_token
REPO_PATH=owner/repo

# LanceDB (可选)
USE_LANCEDB=true
LANCEDB_URI=data/index/.lancedb
```

---

## 故障排查

### Workflow B 无输出
```bash
# 1. 检查订阅源
cat data/subscriptions/x_creators.jsonl
cat data/subscriptions/rss_feeds.jsonl

# 2. 检查 inbox 内容
cat data/inbox/items.jsonl | jq '. | length'

# 3. 检查 API 密钥
cat .env | grep API_KEY

# 4. 查看日志
tail -100 data/logs/$(date +%Y-%m-%d).log
```

### 定时任务未执行
```bash
# 检查服务状态
sudo systemctl status growth-agent

# 查看服务日志
sudo journalctl -u growth-agent -n 100

# 验证配置
cat .env | grep INGESTION_SCHEDULE
```

---

## 去重策略

| Workflow | 去重机制 | 存储模式 |
|----------|----------|---------|
| **A** (GitHub) | Issue number + `updated_at` | 覆盖 |
| **B** (Content) | 无 (每日快照) | 追加+归档 |
| **C** (Metrics) | 无 (总是最新) | 覆盖 |

---

## 核心代码映射

| 功能 | 文件 | 关键函数 |
|------|------|---------|
| 配置管理 | [config.py](src/growth_agent/config.py) | `Settings` |
| 存储 | [storage.py](src/growth_agent/core/storage.py) | `StorageManager` |
| Workflow A | [workflow_a.py](src/growth_agent/workflows/workflow_a.py) | `WorkflowA.execute()` |
| Workflow B | [workflow_b.py](src/growth_agent/workflows/workflow_b.py) | `WorkflowB.execute()` |
| Workflow C | [workflow_c.py](src/growth_agent/workflows/workflow_c.py) | `WorkflowC.execute()` |
| X Ingestor | [x_twitter.py](src/growth_agent/ingestors/x_twitter.py) | `fetch_creator_tweets()` |
| RSS Ingestor | [rss_feed.py](src/growth_agent/ingestors/rss_feed.py) | `fetch_feed_items()` |
| Content Curator | [curator.py](src/growth_agent/processors/curator.py) | `evaluate_items()` |
| Blog Generator | [blog_generator.py](src/growth_agent/processors/blog_generator.py) | `generate_blog()` |
| LLM Client | [llm.py](src/growth_agent/core/llm.py) | `evaluate_content()`, `generate_blog()` |
| Scheduler | [scheduler.py](src/growth_agent/core/scheduler.py) | `run_scheduler()` |

---

**维护者**: HYPERVAPOR
**最后更新**: 2026-02-05
**版本**: 2.0.0

---

> **AI Agent 使用提示**: 本文档专为 AI Agent 设计，强调快速查找和执行对应脚本。当需要实现功能时，直接定位到相关命令执行即可。
