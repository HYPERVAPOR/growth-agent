# PRD: AI Agent 驱动的增长与运营系统 (GROWTH-AGENT)

## 1. 系统概述

本系统旨在建立一套由 AI Agent 驱动的自动化运营流程，核心逻辑基于“文件即存储”的原则，利用 AI 对文件系统的天然亲和力，实现 GitHub 协作、多源情报处理及社交媒体影响力追踪。

## 2. 核心技术栈

* **语言**: Python 3.10+
* **包管理**: `uv` (需包含 `pyproject.toml`)
* **工具链**: GitHub CLI (`gh`), RapidAPI (X Scraper), HTTP Fetch (RSS)
* **存储**: 基于文件系统的结构化存储 (JSONL + Markdown + YAML)
* **LLMs调用**: openrouter
* **向量化**: LanceDB (File-based vector sidecar)

---

## 3. 数据库架构设计 (File-System Database)

### 3.1 存储规范

* **JSONL**: 用于存储高频、结构化记录。支持 Append-only 操作，便于 `tail` 和 `grep`。
* **Markdown + Frontmatter**: 用于存储文章、长描述。AI 友好，支持 `git diff`。
* **Manifest**: 根目录下 `manifest.json` 作为 Data Dictionary，定义各目录的 Schema。

### 3.2 目录拓扑

```text
/data_root
  ├── manifest.json            # 目录索引与操作规范描述
  ├── schemas/                 # 定义各实体的 Markdown 描述文件
  ├── subscriptions/           # 订阅源管理
  │   ├── x_creators.jsonl     # 订阅的 X 博主列表
  │   └── rss_feeds.jsonl      # 订阅的 RSS 源列表
  ├── inbox/                   # 原始采集数据
  │   └── items.jsonl          # X 和 RSS 的统一存储（用 source 字段区分）
  ├── curated/                 # 经过 LLM 筛选后的高价值情报
  │   ├── {YYYY-MM-DD}_ranked.jsonl
  │   └── archives/            # 历史数据
  ├── blogs/                   # 生成的成品内容
  │   └── {ID}_{SLUG}.md       # 包含 YAML Frontmatter 的 Markdown
  ├── github/                  # GitHub Issues 同步数据
  │   └── issues.jsonl
  ├── metrics/                 # 社交媒体互动数据
  │   └── stats.jsonl
  ├── logs/                    # Agent 操作日志 (Daily)
  └── index/                   # 辅助索引文件 (Key-Value mappings)

```

### 3.3 数据库字段定义

#### 3.3.1 subscriptions/x_creators.jsonl
订阅的 X 博主列表，用于管理待追踪的 Twitter/X 账号。

```json
{
  "id": "1234567890",                    // 必需，X 用户的数字 ID（唯一标识）
  "username": "elonmusk",                // 必需，用户名（@ 后面的部分）
  "followers_count": 1000000,            // 必需，粉丝数
  "subscribed_at": "2026-02-05T10:00:00Z", // 必需，订阅时间
  "last_fetched_at": "2026-02-05T12:00:00Z", // 必需，最后抓取时间
}
```

#### 3.3.2 subscriptions/rss_feeds.jsonl
订阅的 RSS 源列表，用于管理待抓取的 RSS/Atom 订阅。

```json
{
  "id": "uuid-v4-string",                // 必需，RSS 源的唯一 ID
  "url": "https://example.com/feed.xml", // 必需，RSS 源 URL
  "title": "Tech Blog",                  // 必需，源标题
  "category": "technology",              // 可选，分类标签
  "language": "en",                      // 可选，内容语言
  "update_frequency": "daily",           // 可选，预期更新频率
  "subscribed_at": "2026-02-05T10:00:00Z", // 必需，订阅时间
  "last_fetched_at": "2026-02-05T12:00:00Z", // 可选，最后抓取时间
  "status": "active"                     // 可选，状态: active/inactive
}
```

#### 3.3.3 inbox/items.jsonl
统一存储 X 和 RSS 的原始采集数据，通过 `source` 字段区分来源。

```json
{
  // === 通用字段（所有来源必备） ===
  "id": "uuid-v4-string",                // 必需，本系统内的唯一 ID
  "source": "x",                         // 必需，来源标识: "x" 或 "rss"
  "original_id": "1234567890",           // 必需，原始平台的内容 ID
  "author_id": "1234567890",             // 必需，作者的 ID（X 为用户 ID，RSS 为 feed_id）
  "author_name": "Author Name",          // 必需，作者名称
  "title": "Content Title",              // 可选，内容标题（X 无此字段）
  "content": "Full content text...",     // 必需，正文内容
  "url": "https://...",                  // 必需，原始链接
  "published_at": "2026-02-05T10:00:00Z", // 必需，发布时间
  "fetched_at": "2026-02-05T12:00:00Z",  // 必需，抓取时间
  "metadata": {...},                     // 可选，来源特定的额外元数据

  // === X 来源特有字段（source="x" 时存在） ===
  "username": "elonmusk",                // X 特有，用户名
  "reply_count": 42,                     // X 特有，回复数
  "retweet_count": 100,                  // X 特有，转推数
  "like_count": 1000,                    // X 特有，点赞数
  "quote_count": 10,                     // X 特有，引用数
  "view_count": 50000,                   // X 特有，浏览数
  "media": ["https://..."],              // X 特有，媒体链接数组
  "hashtags": ["AI", "Tech"],            // X 特有，标签数组

  // === RSS 来源特有字段（source="rss" 时存在） ===
  "feed_id": "uuid-v4-string",           // RSS 特有，所属 feed 的 ID
  "feed_title": "Tech Blog",             // RSS 特有，feed 标题
  "categories": ["tech", "ai"],          // RSS 特有，文章分类
  "excerpt": "Summary text..."           // RSS 特有，摘要/导语
}
```

#### 3.3.4 github/issues.jsonl
GitHub Issues 数据。

```json
{
  "id": 1234567,                         // 必需，Issue 数字 ID
  "node_id": "MDU6SXNzdWUxMjM0NTY3",     // 必需，GitHub node ID
  "title": "Issue title",                // 必需，Issue 标题
  "body": "Issue description...",        // 必需，Issue 内容
  "state": "open",                       // 必需，状态: open/closed
  "author": "username",                  // 必需，作者用户名
  "labels": ["bug", "high-priority"],    // 必需，标签列表
  "created_at": "2026-02-05T10:00:00Z",  // 必需，创建时间
  "updated_at": "2026-02-05T12:00:00Z",  // 必需，更新时间
  "closed_at": null,                     // 可选，关闭时间
  "url": "https://github.com/..."        // 必需，Issue 链接
}
```

#### 3.3.5 metrics/stats.jsonl
社交媒体互动数据。

```json
{
  "id": "uuid-v4-string",                // 必需，记录唯一 ID
  "platform": "x",                       // 必需，平台: x / linkedin
  "content_type": "post",                // 必需，内容类型: post/article
  "content_id": "1234567890",            // 必需，内容 ID
  "url": "https://...",                  // 必需，内容链接
  "impressions": 50000,                  // 可选，展示次数
  "engagements": 2500,                   // 可选，互动总数
  "likes": 1000,                         // 可选，点赞数
  "retweets": 100,                       // 可选，转推数
  "replies": 50,                         // 可选，回复数
  "clicks": 300,                         // 可选，点击数
  "recorded_at": "2026-02-05T12:00:00Z" // 必需，记录时间
}
```

#### 3.3.6 curated/{YYYY-MM-DD}_ranked.jsonl
经过 LLM 筛选和评分的高价值内容。

```json
{
  "id": "uuid-v4-string",                // 必需，本记录唯一 ID
  "source_id": "uuid-v4-string",         // 必需，关联 inbox/items.jsonl 的 id
  "score": 85,                           // 必需，LLM 评分（0-100）
  "summary": "核心总结...",              // 必需，AI 生成的核心总结
  "comment": "入选点评...",              // 必需，AI 给出的入选理由
  "rank": 1,                             // 必需，当日排名
  "curated_at": "2026-02-05T12:00:00Z"  // 必需，筛选时间
}
```

---

## 4. 核心工作流定义 (Workflows)

### Workflow A: GitHub 质量管理

1. **Sync**: 脚本调用 `gh issue list --json` 定期获取仓库 Issues。
2. **Upsert**: 对比本地 `github/issues.jsonl`，更新状态或追加新 Issue。
3. **Action**: Agent 根据 Issue 标签或内容，执行初步分类或指派逻辑。

### Workflow B: 内容情报与 Blog 创作 (核心/高优)

1. **Ingestion (Inbox)**:
* 读取 `subscriptions/x_creators.jsonl` 获取订阅的 X 博主列表。
* 读取 `subscriptions/rss_feeds.jsonl` 获取订阅的 RSS 源列表。
* 每天北京时间8:00，通过 RapidAPI 抓取 X 博主的推文数据、通过 HTTP Fetch 抓取 RSS 源的文章数据。
* 统一写入 `inbox/items.jsonl`，通过 `source` 字段（"x" 或 "rss"）区分来源。
* 更新对应的订阅数据库中的 `last_fetched_at` 字段。


2. **Curation**:
* 读取 `inbox/` 记录。
* **LLM 评估**: 输出 0-100 评分、核心总结、入选点评。
* **过滤机制**: 满足 `Score > 60` 且在 `Top K` 排名内的记录，移至 `curated/`。
* **Cleanup**: 从 `inbox/` 中删除已处理的记录。


3. **Generation (Blog)**:
* 基于 `curated/` 中的单条或多条记录，结合公司产品背景，生成 Markdown 格式 Blog。



### Workflow C: 社交媒体影响力监测

1. **Tracking**: 指定 X/LinkedIn 账号或推文 ID。
2. **Metric Collection**: 获取 Impressions, Likes, Retweets, Clicks。
3. **Storage**: 存入 `metrics/stats.jsonl`，用于后续策略优化。

---

## 5. 环境变量与配置 (`.env.example`)

```bash
# GitHub Configuration
GITHUB_TOKEN=your_token_here
REPO_PATH=owner/repo

# Data API Keys
X-RAPIDAPI-KEY=your_key_here
X-RAPIDAPI-HOST=twitter241.p.rapidapi.com

# LLM Configuration
OPENAI_API_KEY=sk-...

```

---

## 6. 开发要求 (Agent 指导原则)

1. **原子性写入**: 所有的文件写入操作应尽量保证原子性，避免并发写入冲突。
2. **LLM 交互格式**: 在 `curated` 阶段，LLM 必须严格返回结构化 JSON，以便脚本解析评分。
3. **Git 友好**: 所有的存储文件命名需固定，避免产生大量冗余碎片文件，方便 `git diff` 查看数据变化。
4. **无状态设计**: 脚本逻辑应尽量无状态，每次运行通过扫描文件系统确定当前进度。
