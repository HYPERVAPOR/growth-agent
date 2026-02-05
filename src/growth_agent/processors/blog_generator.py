"""
Blog post generator from curated content.

This module generates blog posts using LLM based on curated items.
"""

import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import yaml

from growth_agent.core.llm import LLMClient
from growth_agent.core.schema import BlogFrontmatter, BlogPost, CuratedItem

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        URL-friendly slug
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower()
    # Remove special characters
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    # Replace spaces with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    # Limit length
    slug = slug.strip("-")[:100]
    return slug


class BlogGenerator:
    """
    Blog post generator using LLM.

    Synthesizes curated content into engaging blog posts.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize blog generator.

        Args:
            llm_client: LLM client for content generation
        """
        self.llm = llm_client

    def generate_blog(
        self,
        curated_items: list[CuratedItem],
        context: str = "AI and technology insights for business growth",
    ) -> BlogPost:
        """
        Generate a blog post from curated items.

        Args:
            curated_items: List of curated content items
            context: Optional company/product context

        Returns:
            BlogPost with frontmatter and markdown content
        """
        if not curated_items:
            raise ValueError("No curated items provided for blog generation")

        logger.info(f"Generating blog from {len(curated_items)} curated items")

        # Prepare curated items data
        items_data = [item.model_dump() for item in curated_items]

        # Generate blog content
        content = self.llm.generate_blog(items_data, context)

        # Debug: log raw content (first 500 chars)
        logger.debug(f"Raw LLM output (first 500 chars):\n{content[:500]}")

        # Parse frontmatter and body
        frontmatter, markdown_body = self._parse_frontmatter(content)

        # Generate slug
        title = frontmatter.get("title", "AI Insights Daily")
        slug = slugify(title)

        # Generate ID
        blog_id = str(uuid.uuid4())[:8]

        # Ensure date is in frontmatter
        if "date" not in frontmatter:
            frontmatter["date"] = datetime.now(UTC)

        # Create BlogPost object
        blog_post = BlogPost(
            id=blog_id,
            slug=slug,
            frontmatter=BlogFrontmatter(**frontmatter),
            content=markdown_body,
            source_items=[item.source_id for item in curated_items],
        )

        logger.info(f"Generated blog post: {blog_id} - {title}")
        return blog_post

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """
        Parse YAML frontmatter from LLM output.

        Args:
            content: Full blog content with frontmatter

        Returns:
            Tuple of (frontmatter dict, markdown body)
        """
        # Try to extract frontmatter between --- delimiters
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)

        if match:
            frontmatter_str = match.group(1)
            markdown_body = match.group(2).strip()

            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                # Ensure frontmatter is a dict
                if not isinstance(frontmatter, dict):
                    frontmatter = {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter YAML: {e}")
                frontmatter = {}
                markdown_body = content
        else:
            # No frontmatter found
            frontmatter = {}
            markdown_body = content

        # Set default values if missing
        if "title" not in frontmatter:
            frontmatter["title"] = "AI Insights Daily"
        if "summary" not in frontmatter:
            frontmatter["summary"] = "Daily curated insights on AI and technology trends, breakthroughs, and business applications. Stay informed with the latest developments in artificial intelligence."
        if "tags" not in frontmatter:
            frontmatter["tags"] = ["AI", "Technology"]
        if "author" not in frontmatter:
            frontmatter["author"] = "Growth Agent"

        # Ensure date is datetime object
        if "date" in frontmatter:
            if isinstance(frontmatter["date"], str):
                frontmatter["date"] = datetime.fromisoformat(frontmatter["date"])
        else:
            frontmatter["date"] = datetime.now(UTC)

        return frontmatter, markdown_body
