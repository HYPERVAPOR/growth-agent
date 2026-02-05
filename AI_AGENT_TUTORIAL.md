# 🤖 Growth Agent - AI Agent Tutorial

> **教学目标**: 帮助 AI Agent 理解项目架构、数据库设计，以及如何执行自动化任务

**目录**
- [系统架构](#系统架构)
- [数据库设计](#数据库设计)
- [数据模型详解](#数据模型详解)
- [执行脚本](#执行脚本)
- [实践示例](#实践示例)

---

## 🏗️ 系统架构

### 核心组件

```
Growth Agent
├── 🔧 Configuration (config.py)
│   └── Environment variables → API Keys, Settings
├── 📦 Storage Layer (storage.py)
│   ├── JSONLStore → Line-oriented JSON storage
│   ├── MarkdownStore → Blog post management
│   └── StorageManager → Central coordinator
├── 🔄 Workflows
│   ├── Workflow A → GitHub sync (manual trigger)
│   ├── Workflow B → Content pipeline (scheduled @ 8AM)
│   └── Workflow C → Metrics tracking (manual trigger)
├── 📥 Ingestors
│   ├── X/Twitter → RapidAPI client
│   ├── RSS → Feed parser
│   └── GitHub → gh CLI wrapper
├── 🧠 Processors
│   ├── Curator → LLM content evaluation
│   └── Blog Generator → LLM blog creation
└── ⏰ Scheduler → APScheduler cron triggers
```

### 数据流

```
Ingestion → Curation → Generation
   ↓            ↓            ↓
inbox/    curated/    blogs/
items.jsonl  *_ranked.jsonl  *.md
```

---

## 📊 数据库设计

### 文件系统数据库

Growth Agent 使用 **JSONL (JSON Lines)** 格式作为文件系统数据库：

**特点:**
- ✅ 每行一个 JSON 对象
- ✅ 可读性强，易于调试
- ✅ Git 友好，便于版本控制
- ✅ 原子写入，防止数据损坏

**存储结构:**

```
data/
├── subscriptions/          # 源配置（手动管理）
│   ├── x_creators.jsonl   # X/Twitter 订阅列表
│   └── rss_feeds.jsonl    # RSS 订阅列表
│
├── inbox/                 # 原始内容（每日覆盖）
│   └── items.jsonl        # 所有获取的内容
│
├── curated/               # 精选内容（每日归档）
│   ├── 2026-02-05_ranked.jsonl
│   ├── 2026-02-06_ranked.jsonl
│   └── archives/           # 历史归档
│       └── 2026-02-05_ranked.jsonl
│
├── blogs/                 # 生成的博客文章
│   ├── abc123def_ai_insights.md
│   └── xyz789 Growth Report.md
│
├── github/                # GitHub issues 缓存
│   └── issues.jsonl
│
├── metrics/               # 社交媒体指标
│   └── stats.jsonl
│
├── logs/                  # 执行日志
│   ├── 2026-02-05.log
│   └── 2026-02-06.log
│
└── index/                 # LanceDB 向量索引（可选）
    └── .lancedb/
```

---

## 📋 数据模型详解

### 1. InboxItem - 原始内容基类

**用途**: 存储从 X/Twitter 和 RSS 获取的原始内容

**存储位置**: `data/inbox/items.jsonl`

**JSON 结构:**

```json
{
  "id": "unique-id-123",
  "source": "x",  // "x" 或 "rss"
  "content_type": "post",  // "post" 或 "article"
  "url": "https://x.com/elonmusk/status/123456",
  "content": "这是推文的完整文本内容...",
  "author_name": "Elon Musk",
  "title": null,  // X posts 无标题
  "published_at": "2026-02-05T10:00:00Z",
  "created_at": "2026-02-05T10:05:00Z"
}
```

**关键字段:**
- `id`: 唯一标识符
- `source`: 内容来源
- `content_type`: 内容类型
- `url`: 原始链接
- `content`: 完整文本
- `author_name`: 作者名称

### 2. CuratedItem - AI 精选内容

**用途**: LLM 评分和筛选后的高质量内容

**存储位置**: `data/curated/{YYYY-MM-DD}_ranked.jsonl`

**JSON 结构:**

```json
{
  "id": "unique-id-123",
  "url": "https://x.com/elonmusk/status/123456",
  "author_name": "Elon Musk",
  "title": null,
  "content": "推文内容...",
  "published_at": "2026-02-05T10:00:00Z",
  "source": "x",
  "score": 85,  // ← LLM 评分 (0-100)
  "summary": "这条推文讨论了...",  // ← AI 生成的摘要
  "comment": "观点很有见地，值得深入探讨",  // ← AI 的评价
  "rank": 1,  // ← 排名
  "created_at": "2026-02-05T10:05:00Z"
}
```

**关键字段:**
- `score`: 质量评分 (0-100)
- `summary`: AI 生成的摘要
- `comment`: AI 的专业评价
- `rank`: 在当天内容中的排名

### 3. BlogPost - 生成的博客文章

**用途**: LLM 根据精选内容生成的博客文章

**存储位置**: `data/blogs/{ID}_{slug}.md`

**文件结构:**

```markdown
---
title: AI Insights Daily
date: 2026-02-05T10:00:00Z
summary: Daily curated insights...
tags: [AI, Technology]
author: Growth Agent
---

# Introduction

Today's insights focus on...

## Content Source 1

Elon Musk discusses...

## Conclusion

Stay tuned for more updates...
```

**Frontmatter 字段:**
- `title`: 博客标题
- `date`: 发布日期 (ISO 8601)
- `summary`: 摘要 (50-300 字符)
- `tags`: 标签列表
- `author`: 作者名称

### 4. GitHubIssue - GitHub 问题

**用途**: 从 GitHub 同步的 issues

**存储位置**: `data/github/issues.jsonl`

**JSON 结构:**

```json
{
  "id": 123,
  "node_id": "issue_node_id",
  "title": "Issue title",
  "body": "Issue description...",
  "state": "open",  // "open" 或 "closed"
  "author": "username",
  "labels": ["bug", "enhancement"],
  "created_at": "2026-02-05T10:00:00Z",
  "updated_at": "2026-02-05T12:00:00Z",
  "closed_at": null,
  "url": "https://github.com/repo/issues/123"
}
```

### 5. MetricStat - 社交媒体指标

**用途**: X/Twitter 推文的互动指标

**存储位置**: `data/metrics/stats.jsonl`

**JSON 结构:**

```json
{
  "platform": "x",
  "content_type": "post",
  "content_id": "1234567890",
  "url": "https://x.com/user/status/1234567890",
  "impressions": null,  // 不可用
  "engagements": 150,  // 总互动数
  "likes": 100,
  "retweets": 40,
  "replies": 10,
  "clicks": null
}
```

**计算逻辑:**
```python
engagements = replies + retweets + likes + quotes
```

---

## 🚀 执行脚本

### 1. 初始化项目

```bash
cd /home/hv/projs/growth-agent

# 同步依赖
uv sync

# 初始化数据目录
uv run python -m growth_agent.main init
```

**创建的目录结构:**
```
data/
├── subscriptions/
├── inbox/
├── curated/
├── blogs/
├── github/
├── metrics/
├── logs/
└── index/
```

### 2. 配置订阅源

**2.1 添加 X/Twitter 订阅**

编辑 `data/subscriptions/x_creators.jsonl`:

```json
{"id": "1689650211810123776", "username": "puppyone_ai", "followers_count": 1000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
{"id": "1689650211810123778", "username": "elonmusk", "followers_count": 1000000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

**字段说明:**
- `id`: X User ID (数字字符串)
- `username`: @ 前的用户名
- `followers_count`: 粉丝数
- `subscribed_at`: 订阅时间
- `last_fetched_at`: 最后获取时间 (null 表示未获取)

**2.2 添加 RSS 订阅**

编辑 `data/subscriptions/rss_feeds.jsonl`:

```json
{"id": "techcrunch", "url": "https://techcrunch.com/feed/", "title": "TechCrunch", "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
{"id": "arstechnica", "url": "https://arstechnica.com/feed/", "title": "Ars Technica", "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

### 3. 执行 Workflow B (内容智能管道)

**完整三阶段流程:**

```bash
# 立即执行（手动触发）
uv run python -m growth_agent.main run workflow-b
```

**自动化流程:**

```python
# 阶段 1: Ingestion (获取)
# → 从 X Creators 获取最新 20 条推文
# → 从 RSS Feeds 获取最新 20 篇文章
# → 存储到 data/inbox/items.jsonl

# 阶段 2: Curation (筛选)
# → LLM 评分每个 item (0-100)
# → 过滤低分内容 (score < 60)
# → 选择 Top-10 高质量内容
# → 存储到 data/curated/{日期}_ranked.jsonl

# 阶段 3: Generation (生成)
# → 读取当天的 curated 文件
# → LLM 生成博客文章
# → 保存到 data/blogs/{ID}_{slug}.md
# → 移动 curated 文件到 archives/
```

**预期输出:**

```
✓ Ingested 40 items (20 tweets + 20 articles)
✓ Curated 10 items (score ≥ 60)
✓ Generated 1 blog post
```

### 4. 执行 Workflow A (GitHub 同步)

**手动触发:**

```bash
uv run python scripts/sync_github_issues.py
```

**功能:**
- 使用 `gh issue list` 获取 issues
- Upsert 逻辑：基于 `updated_at` 时间戳
- 覆盖写入：`data/github/issues.jsonl`

**预期输出:**

```
✓ Fetched 23 issues
✓ New: 0, Updated: 0, Unchanged: 23
```

### 5. 执行 Workflow C (社交媒体指标)

**手动触发:**

```bash
uv run python scripts/sync_metrics.py

# 或指定账号
uv run python scripts/sync_metrics.py username user_id
```

**功能:**
- 获取最新 20 条推文
- 提取互动指标 (likes, retweets, replies)
- 覆盖写入：`data/metrics/stats.jsonl`

**预期输出:**

```
✓ Fetched 12 tweets
✓ Total engagements: 2,029
```

### 6. 启动定时任务

**开发机测试 (前台运行):**

```bash
uv run python -m growth_agent.main schedule
# 按 Ctrl+C 停止
```

**服务器部署 (后台服务):**

```bash
# 复制服务文件
sudo cp growth-agent.service.example /etc/systemd/system/growth-agent.service

# 编辑服务配置
sudo vim /etc/systemd/system/growth-agent.service
# 修改 User 和 WorkingDirectory

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable growth-agent
sudo systemctl start growth-agent

# 查看状态
sudo systemctl status growth-agent

# 查看日志
sudo journalctl -u growth-agent -f
```

**定时任务配置 (.env):**

```bash
INGESTION_SCHEDULE=0 8 * * *  # 每天 8:00 AM Beijing
SCHEDULER_TIMEZONE=Asia/Shanghai
```

---

## 🎓 实践示例

### 示例 1: 内容获取流程

**目标**: 从 X/Twitter 获取 @puppyone_ai 的最新推文

**步骤:**

1. **配置订阅源**

```json
{"id": "1689650211810123776", "username": "puppyone_ai", "followers_count": 1000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

2. **执行 Workflow B**

```bash
uv run python -m growth_agent.main run workflow-b
```

3. **查看结果**

```bash
# 查看获取的内容
cat data/inbox/items.jsonl | jq '.[] | {author_name, source, content}'
```

**预期结果:**
- `data/inbox/items.jsonl`: 包含 20 条最新推文
- 自动更新 `last_fetched_at` 时间戳

### 示例 2: 内容筛选流程

**目标**: 理解 LLM 如何筛选和评分内容

**步骤:**

1. **查看筛选结果**

```bash
cat data/curated/2026-02-05_ranked.jsonl | jq '.[] | {score, author_name, summary}'
```

2. **理解评分标准**

```
Score 0-40: 低质量内容
Score 41-60: 中等质量
Score 61-80: 高质量内容
Score 81-100: 优质内容
```

3. **调整筛选阈值** (.env)

```bash
CURATION_MIN_SCORE=70  # 只保留 70 分以上的内容
CURATION_TOP_K=5         # 只选择前 5 条
```

### 示例 3: 博客生成流程

**目标**: 理解 LLM 如何生成博客

**步骤:**

1. **查看精选内容**

```bash
cat data/curated/2026-02-05_ranked.jsonl | jq '.[] | {rank, score, summary}'
```

2. **查看生成的博客**

```bash
ls -lt data/blogs/*.md | head -1
cat data/blogs/abc123def_ai_insights.md
```

3. **理解博客结构**

```markdown
---
title: ...
summary: ...
tags: [...]
---

# Introduction
## Content Source 1
...
## Conclusion
...
```

### 示例 4: 数据查询

**目标**: 如何查询和分析数据

**1. 查看今天的 inbox 内容数量:**

```bash
cat data/inbox/items.jsonl | jq '. | length'
```

**2. 查看某天的精选内容:**

```bash
date="2026-02-05"
cat "data/curated/${date}_ranked.jsonl" | jq '.[] | select(.score > 80)'
```

**3. 统计某个账号的内容数量:**

```bash
cat data/inbox/items.jsonl | jq '[.author_name] | group_by(.) | {count: length}'
```

**4. 查看最近的指标:**

```bash
cat data/metrics/stats.jsonl | jq '.[] | {platform, engagements, likes}'
```

---

## 🔍 故障排查

### 问题 1: Workflow B 没有生成博客

**检查步骤:**

```bash
# 1. 检查 curated 文件
cat data/curated/2026-02-05_ranked.jsonl

# 2. 检查博客生成是否启用
cat .env | grep BLOG_GENERATION_ENABLED

# 3. 查看日志
tail -50 data/logs/$(date +%Y-%m-%d).log | grep -i "generation"
```

### 问题 2: API 调用失败

**检查步骤:**

```bash
# 1. 验证 API 密钥
cat .env | grep API_KEY

# 2. 测试 API 连接
uv run python -c "
from growth_agent.config import reload_settings
from growth_agent.ingestors.x_twitter import XTwitterIngestor

settings = reload_settings()
ingestor = XTwitterIngestor(settings)
tweets = ingestor.fetch_creator_tweets('1689650211810123776', 'puppyone_ai', count=1)
print(f'Fetched {len(tweets)} tweets')
"
```

### 问题 3: 定时任务未执行

**检查步骤:**

```bash
# 1. 检查服务状态
sudo systemctl status growth-agent

# 2. 查看服务日志
sudo journalctl -u growth-agent -n 100

# 3. 验证配置
cat .env | grep INGESTION_SCHEDULE
```

---

## 📚 核心概念总结

### 数据流程

```
Subscriptions → Ingestion → Inbox → Curation → Curated → Generation → Blogs
     ↓              ↓          ↓         ↓           ↓           ↓
  配置文件        获取      存储       评分       存储       生成       存储
```

### 去重策略

| Workflow | 去重机制 | 存储模式 |
|----------|----------|---------|
| **Workflow A** | Issue number + `updated_at` | 覆盖 |
| **Workflow B** | 无 (每日快照) | 追加+归档 |
| **Workflow C** | 无 (总是最新) | 覆盖 |

### 关键函数映射

| 功能 | 文件 | 函数 |
|------|------|------|
| 配置管理 | [config.py](src/growth_agent/config.py) | `Settings` |
| 存储 | [storage.py](src/growth_agent/core/storage.py) | `StorageManager` |
| Workflow A | [workflow_a.py](src/growth_agent/workflows/workflow_a.py) | `WorkflowA.execute()` |
| Workflow B | [workflow_b.py](src/growth_agent/workflows/workflow_b.py) | `WorkflowB.execute()` |
| Workflow C | [workflow_c.py](src/growth_agent/workflows/workflow_c.py) | `WorkflowC.execute()` |
| X Ingestor | [x_twitter.py](src/growth_agent/ingestors/x_twitter.py) | `XTwitterIngestor.fetch_creator_tweets()` |
| Blog Generator | [blog_generator.py](src/growth_agent/processors/blog_generator.py) | `BlogGenerator.generate_blog()` |

---

## 🎯 AI Agent 最佳实践

### 1. 顺序执行

**正确顺序:**

```bash
# 1. 配置订阅源
vim data/subscriptions/x_creators.jsonl
vim data/subscriptions/rss_feeds.jsonl

# 2. 运行内容管道
uv run python -m growth_agent.main run workflow-b

# 3. 验证输出
cat data/blogs/*.md | head -20
```

### 2. 数据验证

**执行后验证:**

```bash
# 检查数据完整性
cat data/inbox/items.jsonl | jq '. | length'
cat data/curated/2026-02-05_ranked.jsonl | jq '. | length'
ls -1 data/blogs/*.md
```

### 3. 日志监控

**实时监控:**

```bash
tail -f data/logs/$(date +%Y-%m-%d).log
```

**搜索错误:**

```bash
grep -i "error\|failed" data/logs/*.log
```

### 4. 配置管理

**修改配置后重启服务:**

```bash
# 修改 .env
vim .env

# 重启服务 (如果是定时任务)
sudo systemctl restart growth-agent
```

---

## 📖 扩展阅读

- [README.md](README.md) - 项目总览
- [data/schemas/](data/schemas/) - 数据模型详细文档
- [growth-agent.service.example](growth-agent.service.example) - 部署配置
- [scheduler.py](src/growth_agent/core/scheduler.py) - 定时任务实现

---

**最后更新**: 2026-02-05
**维护者**: HYPERVAPOR
**版本**: 1.0.0
