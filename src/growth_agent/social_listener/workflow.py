from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from growth_agent.config import Settings
from growth_agent.core.schema import WorkflowResult
from growth_agent.core.storage import StorageManager
from growth_agent.social_listener.config_templates import ensure_default_configs
from growth_agent.social_listener.evaluator import (
    BlogIdeaEvaluator,
    BlogSignalFilter,
    SocialOpportunityEvaluator,
)
from growth_agent.social_listener.fetcher import ContentFilter, RSSFetcher
from growth_agent.social_listener.image_generator import ImageBriefGenerator, QwenImageGenerator
from growth_agent.social_listener.models import BlogOpportunity, Opportunity
from growth_agent.social_listener.notifier import DiscordNotifier
from growth_agent.social_listener.reporter import save_blog_report, save_social_report
from growth_agent.workflows.base import Workflow

logger = logging.getLogger(__name__)


class SocialListenerWorkflow(Workflow):
    def __init__(self, settings: Settings, storage: StorageManager):
        super().__init__(settings, storage)
        self.fetcher = RSSFetcher()
        self.social_filter = ContentFilter()
        self.blog_filter = BlogSignalFilter()
        self.social_evaluator = SocialOpportunityEvaluator(settings)
        self.blog_evaluator = BlogIdeaEvaluator(settings)
        self.image_briefs = ImageBriefGenerator(settings)
        self.image_renderer = None

    def validate_prerequisites(self) -> bool:
        if not self.settings.openrouter_api_key or self.settings.openrouter_api_key == "sk-...":
            logger.error("OpenRouter API key not configured")
            return False
        if self.settings.social_listener_render_images and not self.settings.dashscope_api_key:
            logger.error("DASHSCOPE_API_KEY is required when social_listener_render_images=true")
            return False
        self._ensure_config_files()
        if not self.social_config_path.exists():
            logger.error("Social listener source config not found: %s", self.social_config_path)
            return False
        if not self.blog_config_path.exists():
            logger.error("Social listener blog config not found: %s", self.blog_config_path)
            return False
        return True

    def execute(self) -> WorkflowResult:
        social_sources = self.fetcher.parse_config(self.social_config_path)
        blog_sources = self.fetcher.parse_config(self.blog_config_path)

        social_items = self.fetcher.fetch_all(social_sources, self.settings.social_listener_social_hours)
        social_candidates = self.social_filter.filter(social_items)
        social_candidates = social_candidates[: self.settings.social_listener_social_max_eval]
        social_opportunities = self.social_evaluator.evaluate_batch(social_candidates)
        social_opportunities = [
            item for item in social_opportunities if item.score >= self.settings.social_listener_social_min_score
        ]

        blog_items = self.fetcher.fetch_all(blog_sources, self.settings.social_listener_blog_hours)
        blog_candidates = self.blog_filter.filter(blog_items)
        blog_candidates = blog_candidates[: self.settings.social_listener_blog_max_eval]
        blog_opportunities = self.blog_evaluator.evaluate_batch(blog_candidates)
        blog_opportunities = [
            item for item in blog_opportunities if item.score >= self.settings.social_listener_blog_min_score
        ]

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._generate_assets(run_id, social_opportunities, blog_opportunities)
        social_json, social_md, _ = save_social_report(social_opportunities, self.reports_dir, run_id)
        blog_json, blog_md, _ = save_blog_report(blog_opportunities, self.reports_dir, run_id)

        if self.settings.social_listener_discord_webhook_url:
            self._send_discord_updates(
                social_opportunities=social_opportunities,
                blog_opportunities=blog_opportunities,
                social_report=social_md,
                blog_report=blog_md,
            )

        return WorkflowResult(
            success=True,
            items_processed=len(social_opportunities) + len(blog_opportunities),
            metadata={
                "social_report_json": str(social_json),
                "social_report_md": str(social_md),
                "blog_report_json": str(blog_json),
                "blog_report_md": str(blog_md),
                "social_count": len(social_opportunities),
                "blog_count": len(blog_opportunities),
            },
        )

    def _generate_assets(
        self,
        run_id: str,
        social_opportunities: list[Opportunity],
        blog_opportunities: list[BlogOpportunity],
    ) -> None:
        if self.settings.social_listener_image_count <= 0:
            return
        if self.settings.social_listener_render_images and self.image_renderer is None:
            self.image_renderer = QwenImageGenerator(self.settings)

        for index, opportunity in enumerate(
            social_opportunities[: self.settings.social_listener_image_count],
            start=1,
        ):
            asset = self.image_briefs.generate_x_post(opportunity)
            if self.image_renderer:
                self.image_renderer.render(
                    asset,
                    self.reports_dir / f"puppyone_opportunities_{run_id}_images",
                    f"x_{index}_{opportunity.source_content.get('author', 'post')}",
                )
            opportunity.image_asset = asset.to_dict()

        for index, opportunity in enumerate(
            blog_opportunities[: self.settings.social_listener_image_count],
            start=1,
        ):
            asset = self.image_briefs.generate_blog_cover(opportunity)
            if self.image_renderer:
                self.image_renderer.render(
                    asset,
                    self.reports_dir / f"puppyone_blog_materials_{run_id}_images",
                    f"b_{index}_{opportunity.suggested_title}",
                )
            opportunity.image_asset = asset.to_dict()

    def _send_discord_updates(
        self,
        social_opportunities: list[Opportunity],
        blog_opportunities: list[BlogOpportunity],
        social_report: Path,
        blog_report: Path,
    ) -> None:
        notifier = DiscordNotifier(self.settings.social_listener_discord_webhook_url)
        notifier.send_summary(social_opportunities, blog_opportunities, social_report, blog_report)
        top_k = self.settings.social_listener_notify_top_k
        for index, opportunity in enumerate(social_opportunities[:top_k], start=1):
            notifier.send_social_opportunity(opportunity, index)
        for index, opportunity in enumerate(blog_opportunities[:top_k], start=1):
            notifier.send_blog_opportunity(opportunity, index)

    def _ensure_config_files(self) -> None:
        ensure_default_configs(self.config_dir)

    @property
    def base_dir(self) -> Path:
        return self.storage.data_root / "social_listener"

    @property
    def config_dir(self) -> Path:
        return self.base_dir / "config"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "reports"

    @property
    def social_config_path(self) -> Path:
        if self.settings.social_listener_social_config_path:
            return self.settings.social_listener_social_config_path
        return self.config_dir / "sources.json"

    @property
    def blog_config_path(self) -> Path:
        if self.settings.social_listener_blog_config_path:
            return self.settings.social_listener_blog_config_path
        return self.config_dir / "blog_sources.json"
