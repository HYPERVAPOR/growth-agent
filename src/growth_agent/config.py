"""
Configuration management using pydantic-settings.

This module loads and validates all configuration from environment variables.
"""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SelectionStrategy(str, Enum):
    """Strategy for selecting items from inbox for evaluation."""
    CHRONOLOGICAL = "chronological"  # By write order (original behavior)
    RECENT_FIRST = "recent_first"    # By published_at descending
    RANDOM = "random"                # Random sampling
    BALANCED = "balanced"            # Sample evenly from each source


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        data_root: Root directory for file-system database
        x_rapidapi_key: API key for X/Twitter RapidAPI
        x_rapidapi_host: RapidAPI host for X/Twitter
        openrouter_api_key: API key for OpenRouter (LLM provider)
        github_token: Optional GitHub token for Workflow A
        curation_min_score: Minimum score for content curation (0-100)
        curation_top_k: Maximum number of items to curate per day
        blog_generation_enabled: Whether to generate blog posts
        llm_model: LLM model identifier for OpenRouter
        llm_temperature: Temperature for LLM generation (0.0-1.0)
        llm_max_tokens: Maximum tokens for LLM responses
        lancedb_uri: URI for LanceDB vector store
        scheduler_timezone: Timezone for scheduler
        ingestion_schedule: Cron schedule for ingestion
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # No prefix since env vars are uppercase
        case_sensitive=False,
        extra="ignore",
    )

    # Data paths
    data_root: Path = Field(default=Path("data"), description="Root directory for data storage")

    # API Keys
    x_rapidapi_key: str = Field(..., description="X/Twitter RapidAPI key")
    x_rapidapi_host: str = Field(
        default="twitter241.p.rapidapi.com", description="RapidAPI host for X/Twitter"
    )
    openrouter_api_key: str = Field(..., description="OpenRouter API key for LLM")
    github_token: str | None = Field(default=None, description="GitHub token for Workflow A")
    repo_path: str | None = Field(default=None, description="GitHub repository path (owner/repo) for Workflow A")

    # Google Search Console Configuration
    gsc_enabled: bool = Field(default=False, description="Enable GSC metrics collection")
    gsc_site_url: str | None = Field(default=None, description="GSC site URL (e.g., https://example.com)")
    gsc_service_account_path: str | None = Field(
        default=None, description="Path to GSC service account JSON credentials"
    )
    gsc_client_email: str | None = Field(default=None, description="GSC service account email")
    gsc_private_key: str | None = Field(default=None, description="GSC service account private key")

    # PostHog Configuration
    posthog_enabled: bool = Field(default=False, description="Enable PostHog metrics collection")
    posthog_api_key: str | None = Field(default=None, description="PostHog Personal API Key")
    posthog_host: str = Field(default="app.posthog.com", description="PostHog instance host")
    posthog_project_id: str | None = Field(default=None, description="PostHog project ID")

    # Social Listener Configuration
    social_listener_enabled: bool = Field(default=False, description="Enable daily social listener workflow")
    social_listener_schedule: str = Field(
        default="30 9 * * *",
        description="Cron schedule for the social listener workflow",
    )
    social_listener_social_config_path: Path | None = Field(
        default=None,
        description="Optional path to the social listener social-source config JSON/OPML",
    )
    social_listener_blog_config_path: Path | None = Field(
        default=None,
        description="Optional path to the social listener blog-source config JSON/OPML",
    )
    social_listener_discord_webhook_url: str | None = Field(
        default=None,
        description="Discord webhook URL for daily social listener posts",
    )
    social_listener_social_hours: int = Field(default=24, ge=1, description="Lookback window for social sources")
    social_listener_blog_hours: int = Field(default=72, ge=1, description="Lookback window for blog sources")
    social_listener_social_min_score: int = Field(default=7, ge=0, le=10, description="Min score for social opportunities")
    social_listener_blog_min_score: int = Field(default=7, ge=0, le=10, description="Min score for blog ideas")
    social_listener_social_max_eval: int = Field(default=50, ge=1, description="Max social items to evaluate")
    social_listener_blog_max_eval: int = Field(default=40, ge=1, description="Max blog items to evaluate")
    social_listener_image_count: int = Field(default=1, ge=0, description="How many top items to generate images for")
    social_listener_notify_top_k: int = Field(default=3, ge=1, description="How many top items to send to Discord")
    social_listener_render_images: bool = Field(default=False, description="Render images with qwen-image-2.0")
    social_listener_image_model: str = Field(default="qwen-image-2.0", description="Image generation model name")
    dashscope_api_key: str | None = Field(default=None, description="DashScope API key for qwen-image-2.0")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        description="DashScope base URL",
    )

    # Workflow B Configuration
    curation_min_score: int = Field(
        default=60, ge=0, le=100, description="Minimum score for curation"
    )
    curation_top_k: int = Field(default=10, ge=1, description="Maximum items to curate per day")
    max_curate_items: int = Field(
        default=50, ge=1, description="Maximum inbox items to evaluate with LLM"
    )
    blog_generation_enabled: bool = Field(
        default=True, description="Whether to generate blog posts"
    )

    # Inbox Selection Strategy
    selection_strategy: SelectionStrategy = Field(
        default=SelectionStrategy.RECENT_FIRST,
        description="Strategy for selecting items from inbox for evaluation"
    )
    max_items_per_source_selection: int = Field(
        default=3,
        ge=1,
        description="Max items to sample per source (for BALANCED strategy)"
    )

    # Ingestion Limits (unified control)
    max_items_per_source: int = Field(
        default=20, ge=1, description="Maximum items to fetch per source (X creator or RSS feed)"
    )

    # Deprecated: Use max_items_per_source instead (kept for backward compatibility)
    max_tweets_per_creator: int | None = Field(
        default=None, ge=1, description="DEPRECATED: Use max_items_per_source"
    )
    max_articles_per_feed: int | None = Field(
        default=None, ge=1, description="DEPRECATED: Use max_items_per_source"
    )

    # LLM Configuration
    llm_model: str = Field(
        default="anthropic/claude-3.5-sonnet", description="LLM model identifier"
    )
    llm_temperature: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Temperature for generation"
    )
    llm_max_tokens: int = Field(default=2000, ge=1, description="Maximum tokens in response")

    # LanceDB Configuration
    use_lancedb: bool = Field(default=True, description="Enable LanceDB for fast queries")
    lancedb_uri: str = Field(default="data/index/.lancedb", description="LanceDB database URI")

    # Scheduler Configuration
    scheduler_timezone: str = Field(default="Asia/Shanghai", description="Scheduler timezone")
    ingestion_schedule: str = Field(
        default="0 8 * * *", description="Cron schedule for ingestion (8 AM Beijing)"
    )
    gsc_schedule: str = Field(default="0 9 * * *", description="Cron schedule for GSC metrics (9 AM)")
    posthog_schedule: str = Field(default="0 */6 * * *", description="Cron schedule for PostHog metrics (every 6h)")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    # Prompt Files
    prompts_dir: Path = Field(default=Path("prompts"), description="Directory containing prompt templates")

    @field_validator("data_root")
    @classmethod
    def validate_data_root(cls, v: Path) -> Path:
        """Ensure data_root is absolute path."""
        return v.resolve()

    @field_validator("llm_model")
    @classmethod
    def validate_llm_model(cls, v: str) -> str:
        """
        Validate LLM model identifier.

        Should be in format: provider/model-name
        """
        if "/" not in v:
            raise ValueError(
                'LLM model must be in format "provider/model-name", e.g., "anthropic/claude-3.5-sonnet"'
            )
        return v

    def get_x_api_headers(self) -> dict[str, str]:
        """Get headers for X/Twitter API requests."""
        return {
            "X-RapidAPI-Key": self.x_rapidapi_key,
            "X-RapidAPI-Host": self.x_rapidapi_host,
        }

    def get_openrouter_headers(self) -> dict[str, str]:
        """Get headers for OpenRouter API requests."""
        return {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "https://growth-agent.local",
            "X-Title": "Growth Agent",
        }

    def get_github_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        if not self.github_token:
            raise ValueError("GitHub token not configured")
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_posthog_headers(self) -> dict[str, str]:
        """Get headers for PostHog API requests."""
        if not self.posthog_api_key:
            raise ValueError("PostHog API key not configured")
        return {
            "Authorization": f"Bearer {self.posthog_api_key}",
            "Content-Type": "application/json",
        }


# Global settings instance (will be initialized on first import)
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
