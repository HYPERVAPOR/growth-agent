"""
Configuration management using pydantic-settings.

This module loads and validates all configuration from environment variables.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
