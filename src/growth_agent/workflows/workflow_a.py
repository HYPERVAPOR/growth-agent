"""
Workflow A: GitHub Quality Management.

Syncs GitHub issues to local storage for tracking and analysis.
"""

import logging
from datetime import datetime, UTC
from pathlib import Path

from growth_agent.config import Settings
from growth_agent.core.schema import WorkflowResult, GitHubIssue
from growth_agent.core.storage import StorageManager
from growth_agent.ingestors.github import GitHubIngestor
from growth_agent.workflows.base import Workflow

logger = logging.getLogger(__name__)


class WorkflowA(Workflow):
    """
    GitHub Quality Management workflow.

    Features:
    1. Sync: Fetch issues from GitHub using CLI
    2. Upsert: Update local cache with changes
    3. Track: Maintain issue history in github/issues.jsonl

    Usage:
        workflow = WorkflowA(settings, storage)
        result = workflow.execute()
    """

    def __init__(self, settings: Settings, storage: StorageManager):
        """
        Initialize Workflow A.

        Args:
            settings: Application settings
            storage: Storage manager instance
        """
        self.settings = settings
        self.storage = storage
        self.ingestor = GitHubIngestor(settings)
        self.logger = logger

    def validate_prerequisites(self) -> bool:
        """
        Validate prerequisites for Workflow A.

        Checks:
        - GitHub CLI is available
        - GitHub token is configured
        - Repository path is set

        Returns:
            True if prerequisites are met
        """
        self.logger.info("Validating Workflow A prerequisites...")

        # Check GitHub CLI
        try:
            if not self.ingestor._check_cli_installed():
                self.logger.error("GitHub CLI (gh) is not installed")
                return False
            self.logger.info("✓ GitHub CLI is available")
        except Exception as e:
            self.logger.error(f"Failed to check GitHub CLI: {e}")
            return False

        # Check repository path
        if not self.settings.repo_path:
            self.logger.error("Repository path not configured (REPO_PATH in .env)")
            return False
        self.logger.info(f"✓ Repository: {self.settings.repo_path}")

        # Check GitHub token (optional but recommended)
        if self.settings.github_token:
            self.logger.info("✓ GitHub token is configured")
        else:
            self.logger.warning("⚠ GitHub token not configured (may have rate limit issues)")

        return True

    def execute(
        self,
        state: str = "open",
        limit: int = 100,
    ) -> WorkflowResult:
        """
        Execute GitHub sync workflow.

        Steps:
        1. Fetch issues from GitHub
        2. Load existing issues from github/issues.jsonl
        3. Upsert: Update changed issues, append new ones
        4. Save atomically

        Args:
            state: Issue state to fetch ("open", "closed", "all")
            limit: Maximum number of issues to fetch

        Returns:
            WorkflowResult with sync details
        """
        self.logger.info(f"Starting Workflow A: GitHub sync from {self.settings.repo_path}")

        errors = []
        metadata = {
            "repo": self.settings.repo_path,
            "state": state,
            "limit": limit,
            "synced_at": datetime.now(UTC).isoformat(),
        }

        try:
            # Step 1: Fetch issues from GitHub
            self.logger.info("Fetching issues from GitHub...")
            try:
                fetched_issues = self.ingestor.fetch_issues(
                    repo=self.settings.repo_path,
                    state=state,
                    limit=limit,
                )
                metadata["fetched_count"] = len(fetched_issues)
                self.logger.info(f"Fetched {len(fetched_issues)} issues")
            except Exception as e:
                error_msg = f"Failed to fetch issues: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                return WorkflowResult(
                    success=False,
                    items_processed=0,
                    errors=errors,
                    metadata=metadata,
                )

            # Step 2: Load existing issues
            self.logger.info("Loading existing issues from storage...")
            existing_issues_dict = {}
            try:
                existing_issues_raw = self.storage.read_github_issues()
                # Convert dicts to GitHubIssue objects
                existing_issues = [GitHubIssue(**issue) for issue in existing_issues_raw]
                # Create dict by issue number for easy lookup
                existing_issues_dict = {issue.id: issue for issue in existing_issues}
                metadata["existing_count"] = len(existing_issues)
                self.logger.info(f"Loaded {len(existing_issues)} existing issues")
            except Exception as e:
                self.logger.warning(f"Failed to load existing issues (will create new): {e}")
                metadata["existing_count"] = 0

            # Step 3: Upsert logic
            self.logger.info("Merging issues (upsert logic)...")
            issues_to_write = []
            new_count = 0
            updated_count = 0
            unchanged_count = 0

            for fetched_issue in fetched_issues:
                issue_id = fetched_issue.id

                if issue_id in existing_issues_dict:
                    # Issue exists - check if updated
                    existing_issue = existing_issues_dict[issue_id]

                    # Compare updated_at timestamps
                    if fetched_issue.updated_at > existing_issue.updated_at:
                        # Issue was updated - use fetched version
                        issues_to_write.append(fetched_issue)
                        updated_count += 1
                        self.logger.debug(f"Updated issue #{issue_id}: {fetched_issue.title}")
                    else:
                        # Issue unchanged - keep existing version
                        issues_to_write.append(existing_issue)
                        unchanged_count += 1
                else:
                    # New issue
                    issues_to_write.append(fetched_issue)
                    new_count += 1
                    self.logger.debug(f"New issue #{issue_id}: {fetched_issue.title}")

            metadata["new_count"] = new_count
            metadata["updated_count"] = updated_count
            metadata["unchanged_count"] = unchanged_count

            self.logger.info(f"Merge complete: {new_count} new, {updated_count} updated, {unchanged_count} unchanged")

            # Step 4: Save atomically
            self.logger.info("Saving issues to storage...")
            try:
                # Convert to dict for JSONL storage
                issues_data = [issue.model_dump(mode="json") for issue in issues_to_write]
                self.storage.write_github_issues(issues_data)
                self.logger.info(f"Saved {len(issues_data)} issues to github/issues.jsonl")
            except Exception as e:
                error_msg = f"Failed to save issues: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                return WorkflowResult(
                    success=False,
                    items_processed=len(issues_to_write),
                    errors=errors,
                    metadata=metadata,
                )

            # Success
            self.logger.info("✓ Workflow A completed successfully")
            return WorkflowResult(
                success=True,
                items_processed=len(issues_to_write),
                errors=errors,
                metadata=metadata,
            )

        except Exception as e:
            error_msg = f"Unexpected error in Workflow A: {e}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=errors,
                metadata=metadata,
            )

    def cleanup(self) -> None:
        """Cleanup resources after workflow execution."""
        self.logger.debug("Workflow A cleanup complete")
