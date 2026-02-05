<div align="center">

<h1><img src="images/icon.png" alt="Growth Agent" width="80" height="80" style="vertical-align: middle;"> Growth Agent</h1>

### AI-Powered Content Intelligence & Automated Blog Generation

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude-orange.svg)](https://claude.ai/)
[![AI Agent](https://img.shields.io/badge/AI-Agent-8B5CF6.svg)](https://github.com/HYPERVAPOR/growth-agent)
[![OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-00E599.svg)](https://openrouter.ai/)
[![LanceDB](https://img.shields.io/badge/Vector%20Store-LanceDB-32CD32.svg)](https://lancedb.com/)

**Automated content curation, LLM-powered analysis, and blog generation for modern growth teams**

[Workflows](#-workflows) • [Features](#-features) • [Quick Start](#-quick-start) • [Deployment](#-deployment) • [Development](#-development)

</div>

---

## 🔄 Workflows

<img src="images/workflow%20explained.png" alt="Workflow Explained" width="100%">

### 📦 Workflow A: GitHub Quality Management

**Status:** ✅ Active | **Purpose:** Sync GitHub issues to local storage

```bash
# Manual execution
uv run python scripts/sync_github_issues.py
```

**Features:**
- 🐙 GitHub CLI wrapper (`gh issue list`)
- ⏰ Timestamp-based upsert logic
- 📊 Issue state tracking (open/closed)
- 🔒 Atomic file operations

**Output:** `data/github/issues.jsonl`

---

### 🧠 Workflow B: Content Intelligence & Blog Creation

**Status:** ✅ Active | **Purpose:** Ingest, curate, and generate content

```bash
# Manual execution
uv run python -m growth_agent.main run workflow-b
```

**Three-Stage Pipeline:**

1. **📥 Ingestion Stage**
   - Fetch from X/Twitter creators (20 tweets per creator)
   - Fetch from RSS feeds (20 articles per feed)
   - Store in `data/inbox/items.jsonl`
   - Index in LanceDB for semantic search

2. **🎯 Curation Stage**
   - LLM evaluates each item (score 0-100)
   - Filter by minimum score (default: 60)
   - Select top-K items (default: 10)
   - Store in `data/curated/{date}_ranked.jsonl`

3. **✍️ Generation Stage**
   - LLM generates blog post from curated items
   - YAML frontmatter with metadata
   - Save as `data/blogs/{ID}_{slug}.md`

**Output:**
- 📥 `data/inbox/items.jsonl`
- 🎯 `data/curated/{YYYY-MM-DD}_ranked.jsonl`
- ✍️ `data/blogs/*.md`

---

### 📊 Workflow C: Social Media Metrics Tracking

**Status:** ✅ Active | **Purpose:** Track X/Twitter engagement metrics

```bash
# Manual execution
uv run python scripts/sync_metrics.py

# With custom account
uv run python scripts/sync_metrics.py username user_id
```

**Features:**
- 🐦 Fetch latest 20 tweets from account
- 📈 Extract engagement metrics (likes, retweets, replies)
- 💾 Overwrite mode (keeps latest data only)
- 🔄 No deduplication (always fresh metrics)

**Output:** `data/metrics/stats.jsonl`

---

## ✨ Features

### 🧠 Workflow B - Content Intelligence & Blog Creation
- **📥 Multi-Source Ingestion**
  - 🔗 X/Twitter creators via RapidAPI
  - 📰 RSS feed subscriptions
  - 📊 LanceDB vector indexing for semantic search

- **🎯 AI-Powered Curation**
  - 🤖 LLM-based content evaluation and scoring
  - 📈 Quality filtering (configurable thresholds)
  - 🏆 Top-K selection for high-value content

- **✍️ Automated Blog Generation**
  - 📝 YAML frontmatter with metadata
  - 🎨 GitHub-flavored markdown output
  - 📅 Daily scheduled execution (8 AM Beijing)

### 🔧 Workflow A - GitHub Quality Management
- 🐙 GitHub CLI integration
- 🔄 Automatic issue synchronization
- ⏱️ Timestamp-based upsert logic
- 📂 Local caching with JSONL storage

### 📊 Workflow C - Social Media Metrics
- 🐦 X/Twitter engagement tracking
- 📈 Metrics aggregation (likes, retweets, replies)
- 🔄 Overwrite mode for latest data
- 🎯 Company account monitoring

### 🏗️ Infrastructure
- **⚙️ Configuration**: Pydantic-settings with environment variables
- **💾 Storage**: File-system database with JSONL format
- **📅 Scheduler**: APScheduler with cron triggers
- **📝 Logging**: Structured logging to files and console
- **🔒 Security**: Atomic file operations

---

## 🚀 Quick Start

### 📋 Prerequisites

- **Python** 3.10 or higher
- **uv** (recommended) or pip
- **API Keys**:
  - [X/Twitter RapidAPI Key](https://rapidapi.com/)
  - [OpenRouter API Key](https://openrouter.ai/)
  - GitHub Token (optional, for Workflow A)

### 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/HYPERVAPOR/growth-agent.git
cd growth-agent

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### ⚙️ Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

**Required environment variables:**

```bash
# API Keys
X_RAPIDAPI_KEY=your_x_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional
GITHUB_TOKEN=your_github_token_here
REPO_PATH=puppyone-ai/puppyone

# Scheduler (optional)
SCHEDULER_TIMEZONE=Asia/Shanghai
INGESTION_SCHEDULE=0 8 * * *

# LLM Configuration
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
```

### 🎯 Usage

```bash
# Initialize data directory
uv run python -m growth_agent.main init

# Add subscriptions
vim data/subscriptions/x_creators.jsonl
vim data/subscriptions/rss_feeds.jsonl

# Run Workflow B immediately
uv run python -m growth_agent.main run workflow-b

# Start scheduler daemon (Ctrl+C to stop)
uv run python -m growth_agent.main schedule
```

---

## 📦 Project Structure

```
growth-agent/
├── 📂 src/growth_agent/
│   ├── 📂 core/                  # Core infrastructure
│   │   ├── schema.py            # Pydantic data models
│   │   ├── storage.py           # File-system database
│   │   ├── llm.py               # LLM client (OpenRouter)
│   │   ├── vector_store.py      # LanceDB integration
│   │   ├── logging.py           # Logging configuration
│   │   └── scheduler.py         # APScheduler setup
│   ├── 📂 workflows/             # Workflow orchestration
│   │   ├── base.py              # Abstract workflow base
│   │   ├── workflow_a.py        # GitHub sync
│   │   ├── workflow_b.py        # Content intelligence
│   │   └── workflow_c.py        # Metrics tracking
│   ├── 📂 ingestors/             # Data ingestion
│   │   ├── x_twitter.py         # X/Twitter API client
│   │   ├── rss_feed.py          # RSS feed parser
│   │   ├── github.py            # GitHub CLI wrapper
│   │   └── metrics.py           # Metrics collector
│   ├── 📂 processors/            # Data processing
│   │   ├── curator.py           # LLM content evaluator
│   │   ├── ranker.py            # Content ranking
│   │   └── blog_generator.py    # Blog post generator
│   ├── config.py                # Configuration management
│   └── main.py                  # CLI entry point
├── 📂 data/                      # File-system database
│   ├── subscriptions/           # X/RSS subscriptions
│   ├── inbox/                   # Raw ingested items
│   ├── curated/                 # LLM-evaluated content
│   ├── blogs/                   # Generated blog posts
│   ├── github/                  # GitHub issues cache
│   ├── metrics/                 # Social media metrics
│   ├── logs/                    # Execution logs
│   └── index/                   # LanceDB vector store
├── 📂 scripts/                   # Utility scripts
│   ├── sync_github_issues.py   # Manual Workflow A trigger
│   └── sync_metrics.py         # Manual Workflow C trigger
├── 📂 tests/                     # Test suite
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
└── growth-agent.service.example # systemd service file
```

---

## 🚢 Deployment

### 🖥️ Server Deployment

**1. Clone & Install**

```bash
# Clone repository
git clone https://github.com/HYPERVAPOR/growth-agent.git
cd growth-agent

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

**2. Configure Environment**

```bash
cp .env.example .env
vim .env  # Add your API keys
```

**3. Setup Systemd Service**

```bash
# Copy service file
sudo cp growth-agent.service.example /etc/systemd/system/growth-agent.service

# Edit service (modify User and WorkingDirectory)
sudo vim /etc/systemd/system/growth-agent.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable growth-agent
sudo systemctl start growth-agent

# Check status
sudo systemctl status growth-agent
```

**4. Monitor**

```bash
# View logs
sudo journalctl -u growth-agent -f

# View application logs
tail -f data/logs/$(date +%Y-%m-%d).log
```

### 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Restart service
sudo systemctl restart growth-agent
```

---

## 🧪 Development

### 🏃 Running Tests

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
pytest

# Run with coverage
pytest --cov=src/growth_agent --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 📝 Code Style

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/
```

### 🔍 Debugging

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uv run python -m growth_agent.main run workflow-b --verbose
```

---

## 📊 Data Schemas

### 📥 InboxItem

Base schema for all ingested content.

**Fields:**
- `id`: Unique identifier
- `source`: "x" or "rss"
- `content_type`: "post" or "article"
- `url`: Original URL
- `content`: Text content
- `author_name`: Author display name
- `title`: Content title
- `published_at`: ISO 8601 timestamp

### 🎯 CuratedItem

LLM-evaluated content with quality scores.

**Fields:**
- All InboxItem fields
- `score`: Quality rating (0-100)
- `summary`: AI-generated summary
- `comment`: AI evaluation comment
- `rank`: Position in ranked list

### ✍️ BlogPost

Generated blog post with YAML frontmatter.

**Fields:**
- `id`: Unique blog ID (UUID first 8 chars)
- `slug`: URL-friendly slug
- `title`: Blog title
- `date`: Publication date
- `summary`: Brief summary (50-300 chars)
- `tags`: List of tags
- `author`: Author name
- `content`: Markdown content

See [data/schemas/](data/schemas/) for detailed documentation.

---

## ❓ FAQ

### 🤔 Why JSONL instead of a database?

JSONL (JSON Lines) provides:
- ✅ Simple version control with git
- ✅ Human-readable format
- ✅ Easy debugging and manual inspection
- ✅ No database dependencies
- ✅ Atomic writes prevent corruption

### ⏰ Can I change the schedule time?

Yes! Edit `.env`:
```bash
INGESTION_SCHEDULE=0 9 * * *  # 9 AM instead of 8 AM
```

Cron format: `minute hour day month weekday`

### 🔄 How does deduplication work?

- **Workflow A**: Issue number as unique key, upsert based on `updated_at`
- **Workflow B**: No deduplication (daily snapshots)
- **Workflow C**: Overwrite mode (always latest metrics)

### 📈 Can I track multiple X accounts?

Yes! Add them to `data/subscriptions/x_creators.jsonl`:
```json
{"id": "123456", "username": "elonmusk", "followers_count": 1000000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
{"id": "789012", "username": "puppyone_ai", "followers_count": 1000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

- 📧 Email: support@hypervapor.com
- 🐛 Issues: [GitHub Issues](https://github.com/HYPERVAPOR/growth-agent/issues)
- 📖 Documentation: [data/schemas/](data/schemas/)

---

<div align="center">

**Built with ❤️ by [HYPERVAPOR](https://github.com/HYPERVAPOR)**

</div>
