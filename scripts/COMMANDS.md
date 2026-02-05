# 快速命令参考

## 🚀 手动触发命令

### 完整流程（推荐）
```bash
# 方法1: 使用独立脚本（可分步调试）
uv run python scripts/sync_content.py      # 1. 同步内容
uv run python scripts/curate_content.py     # 2. LLM评估
uv run python scripts/generate_blog.py      # 3. 生成博客

# 方法2: 一键运行所有步骤
uv run python scripts/run_all.sh

# 方法3: 使用CLI
uv run python -m growth_agent.main run workflow-b
```

---

## 📋 分步执行详情

### 1️⃣ 同步内容
```bash
uv run python scripts/sync_content.py
```

**功能**: 从X和RSS获取最新内容（复用Workflow B的业务逻辑）

**输出**: `data/inbox/items.jsonl`

**配置**:
- 每个源最多获取: 5条（可在.env中调整 `MAX_ITEMS_PER_SOURCE`）
- 例如：20个X创作者 + 18个RSS源，最多获取 (20+18)×5 = 190条

**限制控制**:
- 数量限制在 `src/growth_agent/workflows/workflow_b.py` 中统一管理
- 所有业务逻辑在src目录，脚本只是简单调用

---

### 2️⃣ 评估内容
```bash
uv run python scripts/curate_content.py
```

**功能**: LLM评估并筛选高质量内容

**输入**: `data/inbox/items.jsonl`

**输出**: `data/curated/{YYYY-MM-DD}_ranked.jsonl`

**配置**:
- 最低分: 60 (可在.env中调整 `CURATION_MIN_SCORE`)
- 前K名: 10 (可在.env中调整 `CURATION_TOP_K`)

---

### 3️⃣ 生成博客
```bash
uv run python scripts/generate_blog.py
```

**功能**: 生成Markdown博客

**输入**: `data/curated/{YYYY-MM-DD}_ranked.jsonl`

**输出**: `data/blogs/{id}_{slug}.md`

---

## 📊 当前状态

### ✅ 内容获取配置

```bash
# .env配置
MAX_ITEMS_PER_SOURCE=5  # 每个源最多5条
```

**预估数量**:
- X创作者: 20 × 5 = 100条推文
- RSS源: 18 × 5 = 90篇文章
- **总计: 最多190条内容**

---

## 🎯 实际使用建议

### 日常使用（推荐流程）

```bash
# 每天8点自动运行（通过调度器）
uv run python -m growth_agent.main schedule

# 或手动触发完整流程
uv run python scripts/run_all.sh
```

### 分步调试

```bash
# 只测试同步
uv run python scripts/sync_content.py

# 只测试评估（假设已有inbox内容）
uv run python scripts/curate_content.py

# 只测试博客生成（假设已有精选内容）
uv run python scripts/generate_blog.py
```

---

## 🔍 调试技巧

### 查看各阶段数据
```bash
# Inbox数量
wc -l data/inbox/items.jsonl

# Curated文件
ls -lh data/curated/*_ranked.jsonl

# 生成的博客
ls -lh data/blogs/*.md

# 查看日志
tail -50 data/logs/$(date +%Y-%m-%d).log
```

### 查看内容样本
```bash
# 查看inbox前2条（格式化）
head -2 data/inbox/items.jsonl | jq '.'

# 统计来源分布
jq -r '.source' data/inbox/items.jsonl | sort | uniq -c

# 查看精选内容评分
jq '.score' data/curated/*_ranked.jsonl | sort -rn | head -10
```

---

## 💡 常见问题

### Q1: 如何调整获取数量？
A: 编辑 `.env` 文件：
```bash
MAX_ITEMS_PER_SOURCE=10  # 每个源最多10条
```

### Q2: 如何调整评分标准？
A: 编辑 `.env` 文件：
```bash
CURATION_MIN_SCORE=70  # 提高到70分
CURATION_TOP_K=5        # 只保留前5名
```

### Q3: 如何使用中文提示词？
A: 编辑 `prompts/content_evaluation.txt`，改成中文提示词

---

## 📝 下一步

1. **同步内容**:
   ```bash
   uv run python scripts/sync_content.py
   ```

2. **评估内容**:
   ```bash
   uv run python scripts/curate_content.py
   ```

3. **生成博客**:
   ```bash
   uv run python scripts/generate_blog.py
   ```

4. **查看结果**:
   ```bash
   # 查看精选内容
   cat data/curated/$(date +%Y-%m-%d)_ranked.jsonl | jq '.'

   # 查看生成的博客
   ls -lht data/blogs/*.md | head -1
   cat data/blogs/$(ls -t data/blogs/*.md | head -1)
   ```

---

## 🎉 总结

你现在有3种方式触发同步：

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **独立脚本** | `uv run python scripts/sync_content.py` | 测试、调试 |
| **分步执行** | `sync → curate → generate` | 开发、调整参数 |
| **完整流程** | `uv run python scripts/run_all.sh` | 日常使用 |
| **CLI命令** | `uv run python -m growth_agent.main run workflow-b` | 自动化 |

**所有业务逻辑在 `src/` 目录，脚本只是复用这些逻辑。** ✅
