<div align="center">
<h1>Growth Agent: AI-Powered Content Intelligence & Automated Blog Generation</h1>
<img src="images/logo.png" alt="Growth Agent" height="150" style="vertical-align: middle;">

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

### 📊 Workflow C: Social Media & Product Analytics Tracking

**Status:** ✅ Active | **Purpose:** Track engagement metrics across multiple platforms

```bash
# Manual execution - X/Twitter metrics
uv run python scripts/sync_metrics.py --source x

# Google Search Console metrics
uv run python scripts/sync_metrics.py --source gsc --days 7

# PostHog product analytics
uv run python scripts/sync_metrics.py --source posthog --days 1

# Sync all data sources
uv run python scripts/sync_metrics.py --source all
```

**Features:**
- 🐦 **X/Twitter**: Fetch latest tweets and engagement metrics (likes, retweets, replies)
- 🔍 **Google Search Console**: Search analytics, CTR, ranking positions, Core Web Vitals
- 📊 **PostHog**: User behavior events, insights, funnels, feature flags
- 💾 Separate JSONL files per platform (`stats.jsonl`, `gsc_stats.jsonl`, `posthog_stats.jsonl`)
- 🔄 Overwrite mode (keeps latest data only)

**Output:**
- `data/metrics/stats.jsonl` - X/Twitter metrics
- `data/metrics/gsc_stats.jsonl` - Google Search Console data
- `data/metrics/posthog_stats.jsonl` - PostHog analytics data

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

### 📊 Workflow C - Multi-Platform Analytics Tracking
- 🐦 **X/Twitter**: Engagement metrics (likes, retweets, replies, impressions)
- 🔍 **Google Search Console**: SEO performance, search analytics, Core Web Vitals
- 📊 **PostHog**: Product analytics, user events, funnels, insights
- 🔄 Separate storage per platform for efficient querying
- 🎯 OAuth 2.0 and API Key authentication support

### 🏗️ Infrastructure
- **⚙️ Configuration**: Pydantic-settings with environment variables
- **💾 Storage**: File-system database with JSONL format (separate per platform)
- **📅 Scheduling**: Linux cron jobs for production deployments
- **📝 Logging**: Structured logging to files and console
- **🔒 Security**: Atomic file operations, OAuth 2.0, API Key authentication
- **🌐 Multi-Platform**: X/Twitter, GitHub, Google Search Console, PostHog integration

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

# Optional - Workflow A (GitHub)
GITHUB_TOKEN=your_github_token_here
REPO_PATH=puppyone-ai/puppyone

# Optional - Workflow C (Google Search Console)
GSC_ENABLED=true
GSC_SITE_URL=https://example.com
# Option 1: Use service account file
GSC_SERVICE_ACCOUNT_PATH=path/to/service-account.json
# Option 2: Use environment variables (recommended for deployments)
GSC_CLIENT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GSC_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Optional - Workflow C (PostHog)
POSTHOG_ENABLED=true
POSTHOG_API_KEY=phx_your_project_api_key_here  # Use Project API Key, not Personal
POSTHOG_HOST=app.posthog.com
POSTHOG_PROJECT_ID=your_project_id

# LLM Configuration
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
```

### 🔑 Setting up API Keys

**X/Twitter RapidAPI:**
1. Visit [RapidAPI](https://rapidapi.com/)
2. Subscribe to Twitter API v2
3. Copy your API key to `.env`

**OpenRouter:**
1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account and get API key
3. Add to `.env`

**Google Search Console:**
1. Create [Google Cloud Project](https://console.cloud.google.com/)
2. Enable Search Console API
3. Create service account with JSON key
4. Add service account email to GSC property permissions
5. Configure in `.env` (see above)

**PostHog:**
1. Login to [PostHog](https://app.posthog.com/)
2. Navigate to Settings → Project → API Keys
3. Copy **Project API Key** (not Personal API Key)
4. Add to `.env`

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
│   │   ├── metrics.py           # Metrics collector (X/Twitter)
│   │   ├── gsc_search_console.py # Google Search Console API
│   │   └── posthog.py           # PostHog analytics API
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
│   ├── sync_metrics.py         # Manual Workflow C trigger
│   └── test_posthog.py         # PostHog API validation
├── 📂 tests/                     # Test suite
├── pyproject.toml              # Project configuration
└── .env.example                # Environment template
```

---

## 🚢 Deployment

### 🖥️ Server Deployment with Cron Jobs

**1. Clone & Install**

```bash
# Clone repository
git clone https://github.com/HYPERVAPOR/growth-agent.git
cd growth-agent

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Initialize data directory
uv run python -m growth_agent.main init
```

**2. Configure Environment**

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (add API keys)
vim .env
```

**Required environment variables:**

```bash
# API Keys
X_RAPIDAPI_KEY=your_x_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Optional - Workflow A (GitHub)
GITHUB_TOKEN=your_github_token_here
REPO_PATH=puppyone-ai/puppyone

# Optional - Workflow C (GSC & PostHog)
GSC_ENABLED=true
GSC_SITE_URL=https://example.com
GSC_CLIENT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GSC_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

POSTHOG_ENABLED=true
POSTHOG_API_KEY=phx_your_project_api_key_here
POSTHOG_HOST=app.posthog.com
POSTHOG_PROJECT_ID=your_project_id

# LLM Configuration
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
```

**3. Setup Cron Jobs**

```bash
# Edit crontab
crontab -e
```

**Add the following cron jobs:**

```bash
# Workflow A: GitHub Issues Sync (every 2 hours)
0 */2 * * * cd /path/to/growth-agent && /usr/local/bin/uv run python scripts/sync_github_issues.py >> data/logs/cron_workflow_a.log 2>&1

# Workflow B: Content Intelligence & Blog Generation (daily at 8 AM)
0 8 * * * cd /path/to/growth-agent && /usr/local/bin/uv run python -m growth_agent.main run workflow-b >> data/logs/cron_workflow_b.log 2>&1

# Workflow C: X/Twitter Metrics (every 6 hours)
0 */6 * * * cd /path/to/growth-agent && /usr/local/bin/uv run python scripts/sync_metrics.py --source x >> data/logs/cron_workflow_c.log 2>&1

# Workflow C: Google Search Console (daily at 9 AM)
0 9 * * * cd /path/to/growth-agent && /usr/local/bin/uv run python scripts/sync_metrics.py --source gsc --days 7 >> data/logs/cron_workflow_c.log 2>&1

# Workflow C: PostHog Analytics (every 6 hours)
0 */6 * * * cd /path/to/growth-agent && /usr/local/bin/uv run python scripts/sync_metrics.py --source posthog --days 1 >> data/logs/cron_workflow_c.log 2>&1
```

**Important:**
- Replace `/path/to/growth-agent` with your actual project path
- Replace `/usr/local/bin/uv` with your uv executable path (find with `which uv`)
- Adjust schedule times based on your timezone and needs
- Logs are written to `data/logs/cron_workflow_*.log`

**4. Verify Cron Jobs**

```bash
# List current cron jobs
crontab -l

# Check cron service status
sudo systemctl status cron

# View cron logs (Ubuntu/Debian)
sudo grep CRON /var/log/syslog

# View application logs
tail -f data/logs/cron_workflow_b.log
```

**5. Monitor Execution**

```bash
# View workflow logs
tail -f data/logs/$(date +%Y-%m-%d).log

# View specific cron job logs
tail -f data/logs/cron_workflow_a.log  # GitHub sync
tail -f data/logs/cron_workflow_b.log  # Content intelligence
tail -f data/logs/cron_workflow_c.log  # Metrics tracking

# Check last execution time
ls -lh data/blogs/  # Workflow B output
ls -lh data/metrics/  # Workflow C output
ls -lh data/github/  # Workflow A output
```

### 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Reinstall dependencies (if needed)
uv sync

# Test workflows manually
uv run python -m growth_agent.main run workflow-b
uv run python scripts/sync_metrics.py --source all
```

### 🐳 Docker Deployment (Optional)

If you prefer Docker over cron jobs:

```bash
# Build image
docker build -t growth-agent .

# Run with environment file
docker run -d \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --name growth-agent \
  growth-agent
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
- ✅ AI-friendly structure for LLM analysis

### ⏰ How do I change cron job schedules?

Edit your crontab:
```bash
crontab -e
```

Modify the cron schedule format: `minute hour day month weekday`

Examples:
- `0 8 * * *` - Daily at 8 AM
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1` - 9 AM every Monday

### 🔍 How do I get Google Search Console credentials?

1. Create Google Cloud Project
2. Enable Search Console API
3. Create service account & download JSON key
4. Add service account email to GSC property permissions
5. Configure in `.env` (use environment variables for security)

**Helper script available:**
```bash
# Create GSC credentials JSON from environment variables
uv run python scripts/create_gsc_creds.py
```

### 📊 Why does PostHog return 401 Unauthorized?

You're likely using a **Personal API Key** instead of a **Project API Key**.

**Fix:**
1. Login to PostHog
2. Go to Settings → Project → API Keys
3. Copy the **Project API Key** (starts with `phx_`)
4. Update `.env`: `POSTHOG_API_KEY=phx_...`

**Verify:**
```bash
uv run python scripts/test_posthog.py
```

### 🔄 How does deduplication work?

- **Workflow A** (GitHub): Issue number as unique key, upsert based on `updated_at`
- **Workflow B** (Content): No deduplication (daily snapshots with timestamps)
- **Workflow C** (Metrics): Overwrite mode per platform (always latest data)

### 📈 Can I track multiple X accounts?

Yes! Add them to `data/subscriptions/x_creators.jsonl`:
```json
{"id": "123456", "username": "elonmusk", "followers_count": 1000000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
{"id": "789012", "username": "puppyone_ai", "followers_count": 1000, "subscribed_at": "2026-02-05T10:00:00Z", "last_fetched_at": null}
```

### 🚀 Can I run workflows without cron jobs?

Yes! Manual execution:
```bash
# Workflow A
uv run python scripts/sync_github_issues.py

# Workflow B
uv run python -m growth_agent.main run workflow-b

# Workflow C (all platforms)
uv run python scripts/sync_metrics.py --source all

# Workflow C (specific platform)
uv run python scripts/sync_metrics.py --source gsc --days 7
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
