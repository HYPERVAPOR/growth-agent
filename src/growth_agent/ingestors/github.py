"""
GitHub CLI wrapper for issue fetching.
"""

import logging
import subprocess
from datetime import datetime, UTC

from growth_agent.config import Settings
from growth_agent.core.schema import GitHubIssue

logger = logging.getLogger(__name__)


class GitHubIngestor:
    """
    GitHub CLI wrapper for fetching issues.

    Uses 'gh issue list' command to fetch issues from GitHub.
    """

    def __init__(self, settings: Settings):
        """
        Initialize GitHub ingestor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.github_token = settings.github_token

    def _check_cli_installed(self) -> bool:
        """Check if GitHub CLI is installed."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def fetch_issues(
        self,
        repo: str | None = None,
        state: str = "open",
        limit: int = 100,
    ) -> list[GitHubIssue]:
        """
        Fetch issues using GitHub CLI.

        Command: gh issue list --repo {repo} --state {state} --limit {limit} --json {...}

        Args:
            repo: Repository path (owner/repo), defaults to settings.repo_path
            state: Issue state (open/closed/all)
            limit: Maximum number of issues to fetch

        Returns:
            List of GitHubIssue objects
        """
        if not self._check_cli_installed():
            logger.error("GitHub CLI (gh) is not installed")
            raise RuntimeError("GitHub CLI (gh) is not installed. Please install from https://cli.github.com/")

        # Use repo from settings if not provided
        if repo is None:
            repo = self.settings.repo_path

        if not repo:
            raise ValueError("Repository path not configured. Set REPO_PATH in .env or pass repo parameter")

        logger.info(f"Fetching issues from {repo} (state={state}, limit={limit})")

        # Build command
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo", repo,
            "--state", state,
            "--limit", str(limit),
            "--json", "id,number,title,state,author,labels,createdAt,updatedAt,closedAt,url,body",
        ]

        try:
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            # Parse JSON output
            import json
            issues_data = json.loads(result.stdout)

            # Convert to GitHubIssue objects
            issues = []
            for issue_data in issues_data:
                try:
                    issue = self._parse_issue(issue_data)
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to parse issue {issue_data.get('number')}: {e}")
                    continue

            logger.info(f"Fetched {len(issues)} issues from {repo}")
            return issues

        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub CLI failed: {e.stderr}")
            raise RuntimeError(f"Failed to fetch issues: {e.stderr}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GitHub CLI output: {e}")
            raise RuntimeError(f"Invalid JSON output from GitHub CLI") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching issues: {e}")
            raise

    def _parse_issue(self, data: dict) -> GitHubIssue:
        """
        Parse issue data from GitHub CLI output.

        Args:
            data: Raw issue data from GitHub CLI

        Returns:
            GitHubIssue object
        """
        # Parse author
        author_data = data.get("author", {})
        author = author_data.get("login", "unknown")

        # Parse labels
        labels_data = data.get("labels", [])
        labels = [label.get("name", "") for label in labels_data if label.get("name")]

        # Parse timestamps
        created_at = self._parse_timestamp(data.get("createdAt"))
        updated_at = self._parse_timestamp(data.get("updatedAt"))
        closed_at = self._parse_timestamp(data.get("closedAt")) if data.get("closedAt") else None

        # Get body (fallback to empty string)
        body = data.get("body", "")
        if body is None:
            body = ""

        # Normalize state to lowercase (GitHub API returns "OPEN"/"CLOSED")
        state = data.get("state", "open").lower()

        # Create GitHubIssue
        return GitHubIssue(
            id=data["number"],
            node_id=data["id"],
            title=data["title"],
            body=body,
            state=state,
            author=author,
            labels=labels,
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
            url=data["url"],
        )

    def _parse_timestamp(self, timestamp_str: str | None) -> datetime:
        """
        Parse ISO 8601 timestamp from GitHub API.

        Args:
            timestamp_str: ISO 8601 timestamp string

        Returns:
            datetime object
        """
        if not timestamp_str:
            return datetime.now(UTC)

        # GitHub returns timestamps like "2026-02-05T12:00:00Z"
        # Remove trailing 'Z' and add '+00:00' for parsing
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return datetime.fromisoformat(timestamp_str)
